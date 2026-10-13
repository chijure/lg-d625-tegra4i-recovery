import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;
import ghidra.program.model.listing.Instruction;

public class Refs12602 extends GhidraScript {
    @Override
    public void run() throws Exception {
        ReferenceManager refMgr = currentProgram.getReferenceManager();
        Address addr = currentProgram.getImageBase().add(0x12602L);
        ReferenceIterator refs = refMgr.getReferencesTo(addr);
        for (Reference r : refs) {
            Address from = r.getFromAddress();
            Instruction insn = getInstructionAt(from);
            println("from " + from + ": " + insn);
            Instruction cur = insn;
            for (int i=0;i<8 && cur!=null;i++) cur = cur.getPrevious();
            for (int i=0;i<10 && cur!=null;i++) { println("  ctx " + cur.getAddress()+": "+cur); cur = cur.getNext(); }
        }
    }
}
