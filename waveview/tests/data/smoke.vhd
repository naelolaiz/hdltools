-- Source for tests/data/smoke.vcd. Regenerated only when intentionally
-- bumping the snapshot; see waveview/README.md.
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity smoke is
end entity;

architecture sim of smoke is
    signal clk     : std_logic := '0';
    signal counter : unsigned(7 downto 0) := (others => '0');
    signal done    : boolean := false;
begin
    clk <= not clk after 5 ns when not done else '0';

    process(clk)
    begin
        if rising_edge(clk) then
            counter <= counter + 1;
            if counter = x"0F" then
                done <= true;
            end if;
        end if;
    end process;
end architecture;
