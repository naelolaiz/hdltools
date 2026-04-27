// SystemVerilog fixture used by the CI smoke test. Exercises features
// that don't exist in plain Verilog-2005: logic, typedef struct packed,
// struct literals, always_ff, parameterised int widths, default port
// directions. Both linters lint this in CI.
typedef struct packed {
  logic       valid;
  logic [7:0] data;
} entry_t;

module sv_smoke #(
  parameter int W = 8
) (
  input  logic              clk,
  input  logic              rst_n,
  input  logic [W-1:0]      d,
  output logic [W-1:0]      q
);
  entry_t s;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      s <= '{valid: 1'b0, data: '0};
      q <= '0;
    end else begin
      s <= '{valid: 1'b1, data: d};
      q <= s.data;
    end
  end
endmodule
