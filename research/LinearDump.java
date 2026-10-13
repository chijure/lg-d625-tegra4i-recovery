import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;

public class LinearDump extends GhidraScript {
    @Override
    public void run() throws Exception {
        Address start = currentProgram.getImageBase().add(0x12480L);
        Address end = currentProgram.getImageBase().add(0x12610L);
        Instruction insn = getInstructionAt(start);
        while (insn != null && insn.getAddress().compareTo(end) <= 0) {
            println(insn.getAddress() + ": " + insn.toString());
            insn = insn.getNext();
        }
    }
}
