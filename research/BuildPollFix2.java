import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import java.io.FileWriter;
import java.io.PrintWriter;

public class BuildPollFix2 extends GhidraScript {

    static String toHex(byte[] b) {
        StringBuilder sb = new StringBuilder();
        for (byte x : b) sb.append(String.format("%02x", x));
        return sb.toString();
    }

    @Override
    public void run() throws Exception {
        String outPath = new java.io.File(System.getProperty("user.dir"), "out/ghidra/pollfix2_results.txt").getAbsolutePath();
        new java.io.File(outPath).getParentFile().mkdirs();
        PrintWriter out = new PrintWriter(new FileWriter(outPath));

        ghidra.app.plugin.assembler.Assembler asm = ghidra.app.plugin.assembler.Assemblers.getAssembler(currentProgram);

        long STUB_ADDR = 0x4001db22L;
        Address cursor = toAddr(STUB_ADDR);
        Address stubStart = cursor;

        clearListing(cursor, cursor.add(80));
        ghidra.program.model.lang.Register tmodeReg = currentProgram.getProgramContext().getRegister("TMode");
        currentProgram.getProgramContext().setValue(tmodeReg, cursor, cursor.add(80), java.math.BigInteger.ONE);
        for (ghidra.program.model.lang.Register reg : currentProgram.getProgramContext().getContextRegisters()) {
            out.println("context reg: " + reg.getName());
            if (!reg.getName().equals("TMode")) {
                try {
                    currentProgram.getProgramContext().setValue(reg, cursor, cursor.add(80), java.math.BigInteger.ZERO);
                } catch (Exception ig) {}
            }
        }
        out.flush();

        StringBuilder allHex = new StringBuilder();
        try {
            // Replicate FUN_4000f90c's own opening 3 calls (clock/reset enables) so the
            // CLK_RST aperture is safe to touch BEFORE we poll it - this is the fix for
            // today's finding that ANY read of 0x60006xxx hangs before these run.
            String[] pre = new String[] {
                "mov r0,#0x79",
                "mov r1,#0x1",
                "bl 0x4001b478",
                "mov r0,#0x60",
                "mov r1,#0x1",
                "bl 0x4001b478",
                "mov r0,#0x39",
                "mov r1,#0x0",
                "bl 0x4001b648",
                // build r1 = 0x60006090 (real PLLM_BASE, confirmed via LG D625 kernel source
                // tegra14_clocks.c: tegra_pll_m.reg = 0x90)
                "mov r1,#0x60",
                "lsl r1,r1,#8",
                "lsl r1,r1,#8",
                "add r1,#0x60",
                "lsl r1,r1,#8",
                "add r1,#0x90",
                "mov r3,#200",
            };
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

            // locked: call the real SDRAM-init function, then branch back to the call site's
            // own continuation address (0x4001d562 - right after the original "bl 0x400101f2").
            asm.assemble(cursor, "bl 0x400101f2");
            ghidra.program.model.listing.Instruction bI = currentProgram.getListing().getInstructionAt(cursor);
            out.println(cursor + ": bl 0x400101f2 -> " + toHex(bI.getBytes()));
            allHex.append(toHex(bI.getBytes()));
            cursor = cursor.add(bI.getLength());
            out.flush();

            asm.assemble(cursor, "b 0x4001d562");
            ghidra.program.model.listing.Instruction b2 = currentProgram.getListing().getInstructionAt(cursor);
            out.println(cursor + ": b 0x4001d562 -> " + toHex(b2.getBytes()));
            allHex.append(toHex(b2.getBytes()));
            cursor = cursor.add(b2.getLength());
            out.flush();

            out.println("STUB TOTAL LEN = " + (cursor.getOffset() - stubStart.getOffset()));
            out.println("FULL_STUB_BYTES_HEX=" + allHex);
            out.println("STUB_ADDR=0x" + Long.toHexString(STUB_ADDR));

            // call-site patch at bct_process's call to FUN_400101f2 (0x4001d55e): redirect to stub
            Address callSite = toAddr(0x4001d55eL);
            asm.assemble(callSite, "bl 0x" + Long.toHexString(STUB_ADDR));
            ghidra.program.model.listing.Instruction csI = currentProgram.getListing().getInstructionAt(callSite);
            out.println(callSite + ": bl 0x" + Long.toHexString(STUB_ADDR) + " -> " + toHex(csI.getBytes()));
            out.flush();
        } catch (Exception ex) {
            out.println("EXCEPTION: " + ex.getMessage());
            ex.printStackTrace(out);
        }

        out.close();
        println("DONE - wrote " + outPath);
    }
}
