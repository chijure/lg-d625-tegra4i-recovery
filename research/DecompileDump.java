import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import java.io.FileWriter;
import java.io.PrintWriter;

public class DecompileDump extends GhidraScript {
    @Override
    public void run() throws Exception {
        String outPath = new java.io.File(System.getProperty("user.dir"), "out/ghidra/decompile_results.txt").getAbsolutePath();
        new java.io.File(outPath).getParentFile().mkdirs();
        PrintWriter out = new PrintWriter(new FileWriter(outPath));

        DecompInterface decomp = new DecompInterface();
        decomp.openProgram(currentProgram);

        long[] targets = new long[] { 0x4001c130L };

        for (long t : targets) {
            Address a = toAddr(t);
            Function f = getFunctionContaining(a);
            if (f == null) {
                ghidra.program.model.lang.Register tmodeReg = currentProgram.getProgramContext().getRegister("TMode");
                Address rangeEnd = a.add(0x200);
                clearListing(a, rangeEnd);
                currentProgram.getProgramContext().setValue(tmodeReg, a, rangeEnd, java.math.BigInteger.ONE);
                disassemble(a);
                f = createFunction(a, null);
            }
            if (f == null) {
                out.println("NO FUNCTION AT " + a);
                continue;
            }
            out.println("=========== FUNCTION " + f.getName() + " @ " + a + " ===========");
            DecompileResults res = decomp.decompileFunction(f, 60, monitor);
            if (res != null && res.decompileCompleted()) {
                out.println(res.getDecompiledFunction().getC());
            } else {
                out.println("DECOMPILE FAILED: " + (res != null ? res.getErrorMessage() : "null"));
            }
            out.println();
            out.println("--- disassembly ---");
            Address cur = f.getBody().getMinAddress();
            Address end = f.getBody().getMaxAddress();
            while (cur != null && cur.compareTo(end) <= 0) {
                Instruction ins = currentProgram.getListing().getInstructionAt(cur);
                if (ins == null) { cur = cur.add(2); continue; }
                out.println(cur + ": " + ins.toString());
                cur = cur.add(ins.getLength());
            }
            out.println();
            out.flush();
        }

        out.close();
        println("DONE - wrote " + outPath);
    }
}
