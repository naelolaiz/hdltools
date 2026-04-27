// Minimal Verilog used by the CI smoke test to verify that the iverilog v12
// build produces working FST output. Toggles a register a few times and
// dumps to smoke.fst via $dumpfile.
module fst_smoke;
  reg clk = 0;
  initial begin
    $dumpfile("smoke.fst");
    $dumpvars(0, fst_smoke);
    repeat (4) #5 clk = ~clk;
    $finish;
  end
endmodule
