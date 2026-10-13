import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import java.io.FileWriter;
import java.io.PrintWriter;

public class DecompileBctProcess extends GhidraScript {
    @Override
    public void run() throws Exception {
        String outPath = new java.io.File(System.getProperty("user.dir"), "out/ghidra/bct_process_dump.txt").getAbsolutePath();
        new java.io.File(outPath).getParentFile().mkdirs();
        PrintWriter out = new PrintWriter(new FileWriter(outPath));

        DecompInterface decomp = new DecompInterface();
        decomp.openProgram(currentProgram);

        Address a = toAddr(0x4001d55eL);
        Function f = getFunctionContaining(a);
        if (f == null) {
            out.println("NO FUNCTION CONTAINING " + a + " - trying manual disasm/create");
            Address start = toAddr(0x4001d3c0L);
            disassemble(start);
            f = createFunction(start, null);
        }
        if (f == null) {
            out.println("STILL NO FUNCTION");
        } else {
            out.println("FUNCTION " + f.getName() + " @ " + f.getEntryPoint() + " end=" + f.getBody().getMaxAddress());
            DecompileResults res = decomp.decompileFunction(f, 60, monitor);
            if (res != null && res.decompileCompleted()) {
                out.println(res.getDecompiledFunction().getC());
            } else {
                out.println("DECOMPILE FAILED: " + (res != null ? res.getErrorMessage() : "null"));
            }
            out.println("--- disassembly ---");
            Address cur = f.getBody().getMinAddress();
            Address end = f.getBody().getMaxAddress();
            while (cur != null && cur.compareTo(end) <= 0) {
                Instruction ins = currentProgram.getListing().getInstructionAt(cur);
                if (ins == null) { cur = cur.add(2); continue; }
                out.println(cur + ": " + ins.toString());
                cur = cur.add(ins.getLength());
            }
        }
        out.flush();
        out.close();
        println("DONE - wrote " + outPath);
    }
}
