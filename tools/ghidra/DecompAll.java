// Decompile every function of the current program into one text file.
// Headless: analyzeHeadless <proj> <name> -import Heroes3.exe -scriptPath tools/ghidra -postScript DecompAll.java <out.c>
import java.io.PrintWriter;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class DecompAll extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        String out = args.length > 0 ? args[0] : "decomp.c";
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        int done = 0, failed = 0;
        try (PrintWriter w = new PrintWriter(out, "UTF-8")) {
            FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
            while (it.hasNext() && !monitor.isCancelled()) {
                Function f = it.next();
                if (f.isExternal() || f.isThunk()) {
                    continue;
                }
                DecompileResults r = ifc.decompileFunction(f, 120, monitor);
                w.println("//==== " + f.getEntryPoint() + " " + f.getName()
                        + " size=" + f.getBody().getNumAddresses());
                if (r != null && r.decompileCompleted()) {
                    w.println(r.getDecompiledFunction().getC());
                    done++;
                } else {
                    w.println("// decompile failed");
                    failed++;
                }
            }
        }
        println("DecompAll: " + done + " ok, " + failed + " failed -> " + out);
    }
}
