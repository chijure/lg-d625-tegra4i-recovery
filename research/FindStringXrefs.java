import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceManager;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;

public class FindStringXrefs extends GhidraScript {
    @Override
    public void run() throws Exception {
        long[] targets = { 0x9f15dL };
        ReferenceManager refMgr = currentProgram.getReferenceManager();
        FunctionManager fm = currentProgram.getFunctionManager();
        Address base = currentProgram.getImageBase();
        println("Image base: " + base);
        for (long off : targets) {
            Address addr = base.add(off);
            println("=== Target " + addr + " (file offset 0x" + Long.toHexString(off) + ") ===");
            ReferenceIterator refs = refMgr.getReferencesTo(addr);
            for (Reference r : refs) {
                Address from = r.getFromAddress();
                Function f = fm.getFunctionContaining(from);
                println("  from " + from + " in function " + (f != null ? f.getName() + "@" + f.getEntryPoint() : "???"));
            }
        }
    }
}
