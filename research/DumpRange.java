import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;
import java.io.FileWriter;
import java.io.PrintWriter;

public class DumpRange extends GhidraScript {
    @Override
    public void run() throws Exception {
        String outPath = new java.io.File(System.getProperty("user.dir"), "out/ghidra/range_dump.txt").getAbsolutePath();
        new java.io.File(outPath).getParentFile().mkdirs();
        PrintWriter out = new PrintWriter(new FileWriter(outPath));

        long startL = 0x4001d656L;
        long endL = 0x4001d690L;
        Address start = toAddr(startL);
        Address end = toAddr(endL);

        // ensure Thumb mode + disassembled across the range
        ghidra.program.model.lang.Register tmodeReg = currentProgram.getProgramContext().getRegister("TMode");
        try {
            java.math.BigInteger existing = currentProgram.getProgramContext().getValue(tmodeReg, start, false);
            out.println("existing TMode at start: " + existing);
        } catch (Exception e) {}

        clearListing(start, end);
        currentProgram.getProgramContext().setValue(tmodeReg, start, end, java.math.BigInteger.ONE);
        try {
            boolean ok = disassemble(start);
            out.println("disassemble() returned: " + ok);
        } catch (Exception e) {
            out.println("disassemble() threw: " + e);
        }

        Address cur = start;
        while (cur != null && cur.compareTo(end) <= 0) {
            Instruction ins = currentProgram.getListing().getInstructionAt(cur);
            if (ins == null) {
                out.println(cur + ": <no instruction / data / undefined>");
                cur = cur.add(2);
                continue;
            }
            out.println(cur + ": " + ins.toString() + "   [" + ins.getBytes().length + " bytes: " + bytesToHex(ins.getBytes()) + "]");
            cur = cur.add(ins.getLength());
        }

        out.flush();
        out.close();
        println("DONE - wrote " + outPath);
    }

    static String bytesToHex(byte[] b) {
        StringBuilder sb = new StringBuilder();
        for (byte x : b) sb.append(String.format("%02x", x));
        return sb.toString();
    }
}
