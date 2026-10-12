// Dump the listing of selected functions, annotating FPU memory operands with their constant values.
// Headless: analyzeHeadless <proj> <name> -process Heroes3.exe -noanalysis -scriptPath tools/ghidra -postScript DumpAsm.java <out.txt> <addr> [<addr>...]
import java.io.PrintWriter;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;

public class DumpAsm extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        Memory mem = currentProgram.getMemory();
        try (PrintWriter w = new PrintWriter(args[0], "UTF-8")) {
            for (int i = 1; i < args.length; i++) {
                Function f = getFunctionAt(toAddr(args[i]));
                if (f == null) {
                    w.println("//==== " + args[i] + " no function");
                    continue;
                }
                w.println("//==== " + f.getEntryPoint());
                InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
                while (it.hasNext()) {
                    Instruction ins = it.next();
                    StringBuilder line = new StringBuilder(ins.getAddress() + " " + ins);
                    String m = ins.getMnemonicString();
                    if (m.startsWith("F")) {
                        for (Reference r : ins.getReferencesFrom()) {
                            Address a = r.getToAddress();
                            if (!r.isMemoryReference() || !mem.contains(a) || mem.getBlock(a).isExecute()) {
                                continue;
                            }
                            String s = ins.toString();
                            try {
                                if (s.contains("qword") || s.contains("double")) {
                                    line.append("   ; ").append(Double.longBitsToDouble(mem.getLong(a)));
                                } else if (s.contains("dword") || s.contains("float")) {
                                    if (m.startsWith("FI")) {
                                        line.append("   ; int ").append(mem.getInt(a));
                                    } else {
                                        line.append("   ; ").append(Float.intBitsToFloat(mem.getInt(a)));
                                    }
                                }
                            } catch (Exception e) {
                                // uninitialised memory: no constant to show
                            }
                        }
                    }
                    w.println(line);
                }
            }
        }
    }
}
