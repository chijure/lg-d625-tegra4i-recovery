import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;
import ghidra.program.model.listing.Instruction;

public class FindBlockXrefs extends GhidraScript {
    @Override
    public void run() throws Exception {
        long[] targets = {0x1264eL, 0x123a0L};
        ReferenceManager refMgr = currentProgram.getReferenceManager();
        for (long t : targets) {
            Address addr = currentProgram.getImageBase().add(t);
            println("=== refs to " + addr + " ===");
            ReferenceIterator refs = refMgr.getReferencesTo(addr);
            for (Reference r : refs) {
                Address from = r.getFromAddress();
                Instruction insn = getInstructionAt(from);
                println("  from " + from + ": " + (insn != null ? insn.toString() : "?"));
                // print a few instructions before to see the compare
                Instruction cur = insn;
                for (int i = 0; i < 6 && cur != null; i++) {
                    cur = cur.getPrevious();
                }
                for (int i = 0; i < 8 && cur != null; i++) {
                    println("      ctx " + cur.getAddress() + ": " + cur.toString());
                    cur = cur.getNext();
                }
            }
        }
    }
}
