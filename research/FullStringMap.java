import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Data;

public class FullStringMap extends GhidraScript {
    @Override
    public void run() throws Exception {
        ReferenceManager refMgr = currentProgram.getReferenceManager();
        FunctionManager fm = currentProgram.getFunctionManager();
        Data d = getFirstData();
        int total = 0;
        while (d != null) {
            if (d.hasStringValue()) {
                total++;
                String val;
                try { val = (String) d.getValue(); } catch (Exception e) { d = getDataAfter(d); continue; }
                if (val == null) { d = getDataAfter(d); continue; }
                String lower = val.toLowerCase();
                if (lower.contains("secur") || lower.contains("verif") || lower.contains("signat") ||
                    lower.contains("boot") || lower.contains("rsa") || lower.contains("hash") ||
                    lower.contains("sha1") || lower.contains("sha256") || lower.contains("crc") || lower.contains("cert")) {
                    ReferenceIterator refs = refMgr.getReferencesTo(d.getAddress());
                    StringBuilder callers = new StringBuilder();
                    for (Reference r : refs) {
                        Function f = fm.getFunctionContaining(r.getFromAddress());
                        callers.append(f != null ? f.getEntryPoint().toString() : r.getFromAddress().toString()).append(" ");
                    }
                    println(d.getAddress() + " | " + val.replace("\n","\\n") + " | callers: " + (callers.length()>0? callers.toString(): "NONE"));
                }
            }
            d = getDataAfter(d);
        }
        println("Total defined data items scanned: " + total);
    }
}
