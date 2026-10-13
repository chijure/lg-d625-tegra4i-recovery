import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;

public class FindBootSig extends GhidraScript {
    @Override
    public void run() throws Exception {
        ReferenceManager refMgr = currentProgram.getReferenceManager();
        FunctionManager fm = currentProgram.getFunctionManager();
        long[] strAddrs = {0x9e99eL, 0x9e9adL, 0x9e965L, 0x9e9caL};
        for (long sa : strAddrs) {
            Address addr = currentProgram.getImageBase().add(sa);
            println("=== refs to string @ 0x" + Long.toHexString(sa) + " ===");
            ReferenceIterator refs = refMgr.getReferencesTo(addr);
            boolean any=false;
            for (Reference r : refs) {
                any=true;
                Address from = r.getFromAddress();
                Instruction insn = getInstructionAt(from);
                Function f = fm.getFunctionContaining(from);
                println("  from " + from + ": " + insn + "  in " + (f!=null? f.getName()+"@"+f.getEntryPoint() : "?"));
            }
            if(!any) println("  (ninguna)");
        }
        // callers of key funcs
        long[] funcs = {0x123a0L, 0x15838L, 0xe528L};
        for (long fa : funcs) {
            Address a = currentProgram.getImageBase().add(fa);
            println("=== callers of FUN @ 0x" + Long.toHexString(fa) + " ===");
            ReferenceIterator refs2 = refMgr.getReferencesTo(a);
            for (Reference r : refs2) {
                Address from = r.getFromAddress();
                Function f = fm.getFunctionContaining(from);
                println("  from " + from + " in " + (f!=null? f.getName()+"@"+f.getEntryPoint() : "?") + "  (" + r.getReferenceType() + ")");
            }
        }
    }
}
