import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.util.task.ConsoleTaskMonitor;

public class DecompileAddr extends GhidraScript {
    @Override
    public void run() throws Exception {
        long[] targets = {0xe528L};
        DecompInterface decomp = new DecompInterface();
        decomp.openProgram(currentProgram);
        for (long t : targets) {
            Address addr = currentProgram.getImageBase().add(t);
            Function f = currentProgram.getFunctionManager().getFunctionAt(addr);
            if (f == null) {
                println("No function at " + addr);
                continue;
            }
            DecompileResults res = decomp.decompileFunction(f, 60, new ConsoleTaskMonitor());
            println("=== DECOMPILED " + f.getName() + " @ " + f.getEntryPoint() + " ===");
            println(res.getDecompiledFunction().getC());
        }
    }
}
