import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.scalar.Scalar;
import java.io.FileWriter;
import java.io.PrintWriter;

public class SearchConstants extends GhidraScript {
    @Override
    public void run() throws Exception {
        String outPath = new java.io.File(System.getProperty("user.dir"), "out/ghidra/search_constants_result.txt").getAbsolutePath();
        new java.io.File(outPath).getParentFile().mkdirs();
        PrintWriter out = new PrintWriter(new FileWriter(outPath));

        long[] targets = new long[] { 0x70000000L, 0x70000804L, 0x60006000L, 0x60006090L };

        Instruction ins = getFirstInstruction();
        int count = 0;
        while (ins != null) {
            int n = ins.getNumOperands();
            for (int i = 0; i < n; i++) {
                Object[] objs = ins.getOpObjects(i);
                for (Object o : objs) {
                    if (o instanceof Scalar) {
                        long v = ((Scalar) o).getUnsignedValue();
                        for (long t : targets) {
                            if (v == t) {
                                out.println(ins.getAddress() + ": " + ins.toString() + "   [match 0x" + Long.toHexString(t) + "]");
                                count++;
                            }
                        }
                    }
                }
            }
            ins = ins.getNext();
        }
        out.println("TOTAL MATCHES: " + count);
        out.flush();
        out.close();
        println("DONE - wrote " + outPath);
    }
}
