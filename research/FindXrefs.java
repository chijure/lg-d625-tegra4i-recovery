import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import java.io.FileWriter;
import java.io.PrintWriter;

public class FindXrefs extends GhidraScript {

    static String toHex(byte[] b) {
        StringBuilder sb = new StringBuilder();
        for (byte x : b) sb.append(String.format("%02x", x));
        return sb.toString();
    }

    @Override
    public void run() throws Exception {
        String outPath = new java.io.File(System.getProperty("user.dir"), "out/ghidra/xref_results.txt").getAbsolutePath();
        new java.io.File(outPath).getParentFile().mkdirs();
        PrintWriter out = new PrintWriter(new FileWriter(outPath));

        ghidra.app.plugin.assembler.Assembler asm = ghidra.app.plugin.assembler.Assemblers.getAssembler(currentProgram);

        long STUB_ADDR = 0x4001db22L;
        Address cursor = toAddr(STUB_ADDR);
        Address stubStart = cursor;

        clearListing(cursor, cursor.add(74));
        ghidra.program.model.lang.Register tmodeReg = currentProgram.getProgramContext().getRegister("TMode");
        currentProgram.getProgramContext().setValue(tmodeReg, cursor, cursor.add(74), java.math.BigInteger.ONE);

        try {
            // stub: restore true lr from r12, poll, then replicate the 3 stolen entry instructions
            // (push{r4,r5,r6,lr}; mov r5,r0; mov r0,#0xb), then resume at the 4th original instruction.
            String[] pre = new String[] {
                "mov lr,r12",
                "mov r1,#0x60",
                "lsl r1,r1,#8",
                "lsl r1,r1,#8",
                "add r1,#0x61",
                "lsl r1,r1,#8",
                "add r1,#0x80",
                "mov r3,#200",
            };
            StringBuilder allHex = new StringBuilder();
            for (String line : pre) {
                asm.assemble(cursor, line);
                ghidra.program.model.listing.Instruction ins = currentProgram.getListing().getInstructionAt(cursor);
                out.println(cursor + ": '" + line + "' -> " + toHex(ins.getBytes()));
                allHex.append(toHex(ins.getBytes()));
                cursor = cursor.add(ins.getLength());
                out.flush();
            }

            Address pollLabel = cursor;
            String[] pollLines = new String[] { "ldr r2,[r1,#0]", "lsl r2,r2,#4", "cmp r2,#0" };
            for (String line : pollLines) {
                asm.assemble(cursor, line);
                ghidra.program.model.listing.Instruction ins = currentProgram.getListing().getInstructionAt(cursor);
                out.println(cursor + ": '" + line + "' -> " + toHex(ins.getBytes()));
                allHex.append(toHex(ins.getBytes()));
                cursor = cursor.add(ins.getLength());
                out.flush();
            }

            Address bmiAddr = cursor;
            cursor = cursor.add(2);

            asm.assemble(cursor, "sub r3,#1");
            ghidra.program.model.listing.Instruction si = currentProgram.getListing().getInstructionAt(cursor);
            out.println(cursor + ": sub r3,#1 -> " + toHex(si.getBytes()));
            allHex.append(toHex(si.getBytes()));
            cursor = cursor.add(si.getLength());
            out.flush();

            asm.assemble(cursor, "bne 0x" + pollLabel.toString(false));
            ghidra.program.model.listing.Instruction bnI = currentProgram.getListing().getInstructionAt(cursor);
            out.println(cursor + ": bne " + pollLabel + " -> " + toHex(bnI.getBytes()));
            allHex.append(toHex(bnI.getBytes()));
            cursor = cursor.add(bnI.getLength());
            out.flush();

            Address lockedAddr = cursor;
            asm.assemble(bmiAddr, "bmi 0x" + lockedAddr.toString(false));
            ghidra.program.model.listing.Instruction bmiI = currentProgram.getListing().getInstructionAt(bmiAddr);
            out.println(bmiAddr + ": bmi " + lockedAddr + " -> " + toHex(bmiI.getBytes()));
            out.flush();

            // Replicate the 3 stolen original instructions verbatim (raw bytes):
            // push {r4,r5,r6,lr} (70b5) ; mov r5,r0 (0500) ; mov r0,#0xb (0b20)
            byte[] stolen = new byte[] { 0x70, (byte)0xb5, 0x05, 0x00, 0x0b, 0x20 };
            currentProgram.getMemory().setBytes(cursor, stolen);
            currentProgram.getListing().clearCodeUnits(cursor, cursor.add(5), false);
            disassemble(cursor);
            for (Address a2 = cursor; a2.compareTo(cursor.add(5)) < 0; ) {
                ghidra.program.model.listing.Instruction si2 = currentProgram.getListing().getInstructionAt(a2);
                if (si2 == null) break;
                out.println(a2 + ": (stolen) " + si2.toString());
                a2 = a2.add(si2.getLength());
            }
            allHex.append(toHex(stolen));
            cursor = cursor.add(stolen.length);
            out.flush();

            // Resume at the 4th original instruction (0x400101fa: "add r4,r5,r0") via bl (safe: the
            // correct lr is already saved on the stack by the just-replicated push).
            asm.assemble(cursor, "bl 0x400101f8");
            ghidra.program.model.listing.Instruction bI = currentProgram.getListing().getInstructionAt(cursor);
            out.println(cursor + ": bl 0x400101f8 -> " + toHex(bI.getBytes()));
            allHex.append(toHex(bI.getBytes()));
            cursor = cursor.add(bI.getLength());
            out.flush();

            out.println("STUB TOTAL LEN = " + (cursor.getOffset() - stubStart.getOffset()) + " (budget: 75 bytes)");

            StringBuilder fullHex = new StringBuilder();
            Address p = stubStart;
            while (p.compareTo(cursor.subtract(1)) <= 0) {
                byte b = currentProgram.getMemory().getByte(p);
                fullHex.append(String.format("%02x", b));
                p = p.add(1);
            }
            out.println("FULL_STUB_BYTES_HEX=" + fullHex);
            out.println("STUB_ADDR=0x" + Long.toHexString(STUB_ADDR));

            // ENTRY patch: steal 3 original instructions (6 bytes: push, mov r5 r0, mov r0 #0xb) at
            // 0x400101f2, replace with "mov r12,lr; bl <stub>" (2+4=6 bytes exact fit).
            Address entrySite = toAddr(0x400101f2L);
            asm.assemble(entrySite, "mov r12,lr");
            ghidra.program.model.listing.Instruction e1 = currentProgram.getListing().getInstructionAt(entrySite);
            out.println(entrySite + ": mov r12,lr -> " + toHex(e1.getBytes()));
            Address entryCursor = entrySite.add(e1.getLength());
            out.flush();

            asm.assemble(entryCursor, "bl 0x" + Long.toHexString(STUB_ADDR));
            ghidra.program.model.listing.Instruction e2 = currentProgram.getListing().getInstructionAt(entryCursor);
            out.println(entryCursor + ": bl 0x" + Long.toHexString(STUB_ADDR) + " -> " + toHex(e2.getBytes()) + " len=" + e2.getLength());
            out.println("ENTRY_TOTAL_LEN=" + (e1.getLength() + e2.getLength()) + " (budget: 6 bytes)");
        } catch (Exception ex) {
            out.println("EXCEPTION: " + ex.getMessage());
        }

        out.close();
        println("DONE - wrote " + outPath);
    }
}
