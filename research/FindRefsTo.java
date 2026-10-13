import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import java.io.FileWriter;
import java.io.PrintWriter;

public class FindRefsTo extends GhidraScript {
    @Override
    public void run() throws Exception {
        String outPath = new java.io.File(System.getProperty("user.dir"), "out/ghidra/refs_to_result.txt").getAbsolutePath();
        new java.io.File(outPath).getParentFile().mkdirs();
        PrintWriter out = new PrintWriter(new FileWriter(outPath));

        long[] targets = new long[] { 0x4001aec8L, 0x4001aeccL };
        for (long t : targets) {
            Address a = toAddr(t);
            out.println("References TO " + a + ":");
            ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(a);
            boolean any = false;
            while (it.hasNext()) {
                Reference r = it.next();
                out.println("  from " + r.getFromAddress() + " type=" + r.getReferenceType());
                any = true;
            }
            if (!any) out.println("  (none found)");
        }

        out.flush();
        out.close();
        println("DONE - wrote " + outPath);
    }
}
