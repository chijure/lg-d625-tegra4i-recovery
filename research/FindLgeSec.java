import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;

public class FindLgeSec extends GhidraScript {
    @Override
    public void run() throws Exception {
        ReferenceManager refMgr = currentProgram.getReferenceManager();
        FunctionManager fm = currentProgram.getFunctionManager();
        Address addr = currentProgram.getImageBase().add(0x9e9adL);
        println("=== refs to [LGE_SECURITY] ERROR string @ " + addr + " ===");
        ReferenceIterator refs = refMgr.getReferencesTo(addr);
        for (Reference r : refs) {
            Address from = r.getFromAddress();
            Instruction insn = getInstructionAt(from);
            Function f = fm.getFunctionContaining(from);
            println("from " + from + ": " + insn + "  in function " + (f!=null? f.getName()+"@"+f.getEntryPoint() : "?"));
        }
        // also check callers of FUN_000123a0
        Address ebt123a0 = currentProgram.getImageBase().add(0x123a0L);
        Function target = fm.getFunctionAt(ebt123a0);
        println("=== callers of FUN_000123a0 ===");
        ReferenceIterator refs2 = refMgr.getReferencesTo(ebt123a0);
        for (Reference r : refs2) {
            Address from = r.getFromAddress();
            Function f = fm.getFunctionContaining(from);
            println("called from " + from + " in function " + (f!=null? f.getName()+"@"+f.getEntryPoint() : "?"));
        }
    }
}
