import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Instruction;
import java.io.FileWriter;
import java.io.PrintWriter;

public class DumpAllDisasm extends GhidraScript {
    @Override
    public void run() throws Exception {
        String outPath = new java.io.File(System.getProperty("user.dir"), "out/ghidra/full_disasm_dump.txt").getAbsolutePath();
        new java.io.File(outPath).getParentFile().mkdirs();
        PrintWriter out = new PrintWriter(new FileWriter(outPath));
        Instruction ins = getFirstInstruction();
        while (ins != null) {
            out.println(ins.getAddress() + ": " + ins.toString());
            ins = ins.getNext();
        }
        out.flush();
        out.close();
        println("DONE - wrote " + outPath);
    }
}
