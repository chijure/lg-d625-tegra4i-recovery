import ghidra.app.script.GhidraScript;

public class CountFuncs extends GhidraScript {
    @Override
    public void run() throws Exception {
        println("function count: " + currentProgram.getFunctionManager().getFunctionCount());
    }
}
