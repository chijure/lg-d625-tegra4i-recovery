import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;

public class CallersOf extends GhidraScript {
    @Override
    public void run() throws Exception {
        long[] targets = {0x15838L, 0xe528L};
        ReferenceManager refMgr = currentProgram.getReferenceManager();
        FunctionManager fm = currentProgram.getFunctionManager();
        for (long t : targets) {
            Address addr = currentProgram.getImageBase().add(t);
            println("=== callers of " + addr + " ===");
            ReferenceIterator refs = refMgr.getReferencesTo(addr);
            for (Reference r : refs) {
                Function f = fm.getFunctionContaining(r.getFromAddress());
                println("  from " + r.getFromAddress() + " in " + (f!=null?f.getName()+"@"+f.getEntryPoint():"?"));
            }
        }
    }
}
