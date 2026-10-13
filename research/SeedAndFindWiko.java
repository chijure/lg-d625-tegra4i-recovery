import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.cmd.function.CreateFunctionCmd;

public class SeedAndFindWiko extends GhidraScript {
    @Override
    public void run() throws Exception {
        Address entry = currentProgram.getImageBase().add(0x64L);
        DisassembleCommand dis = new DisassembleCommand(entry, null, true);
        dis.applyTo(currentProgram);
        CreateFunctionCmd cf = new CreateFunctionCmd(entry);
        cf.applyTo(currentProgram);
        println("Seeded function at " + entry);

        ReferenceManager refMgr = currentProgram.getReferenceManager();
        FunctionManager fm = currentProgram.getFunctionManager();
        Address addr = currentProgram.getImageBase().add(0x8e51dL);
        println("=== refs to VerifySignature string @ " + addr + " ===");
        ReferenceIterator refs = refMgr.getReferencesTo(addr);
        int count = 0;
        for (Reference r : refs) {
            Function f = fm.getFunctionContaining(r.getFromAddress());
            println("from " + r.getFromAddress() + " in " + (f!=null? f.getName()+"@"+f.getEntryPoint() : "?"));
            count++;
        }
        println("total refs: " + count);
    }
}
