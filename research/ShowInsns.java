import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;

public class ShowInsns extends GhidraScript {
    @Override
    public void run() throws Exception {
        long[] targets = {0x12602L, 0x12656L, 0x1265aL};
        for (long t : targets) {
            Address center = currentProgram.getImageBase().add(t);
            println("=== around " + center + " ===");
            Address start = center.subtract(0x20);
            Instruction insn = getInstructionAt(start);
            if (insn == null) insn = getInstructionContaining(start);
            int count = 0;
            while (insn != null && count < 20) {
                String marker = insn.getAddress().equals(center) ? " <<<<" : "";
                println(insn.getAddress() + ": " + insn.toString() + marker);
                if (insn.getAddress().getOffset() > center.getOffset() + 0x10) break;
                insn = insn.getNext();
                count++;
            }
        }
    }
}
