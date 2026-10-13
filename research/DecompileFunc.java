import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.util.task.ConsoleTaskMonitor;

public class DecompileFunc extends GhidraScript {
    @Override
    public void run() throws Exception {
        Address addr = currentProgram.getImageBase().add(0x123a0);
        Function f = currentProgram.getFunctionManager().getFunctionAt(addr);
        if (f == null) {
            println("No function found at " + addr);
            return;
        }
        DecompInterface decomp = new DecompInterface();
        decomp.openProgram(currentProgram);
        DecompileResults res = decomp.decompileFunction(f, 60, new ConsoleTaskMonitor());
        println("=== DECOMPILED " + f.getName() + " @ " + f.getEntryPoint() + " ===");
        println(res.getDecompiledFunction().getC());
    }
}
