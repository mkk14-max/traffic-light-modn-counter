"""
Gate-level check of the traffic light controller design (pure Python, no libraries).

It models the exact gates used in the README:
  - 4-bit synchronous counter with synchronous clear (like 74HC163)
  - clear logic  CLR' = NAND(D, OR(C, AND(B,A)))        -> MOD-12
  - output logic built from AND / OR / NOR / XOR / NOT gates
and checks every state, the sequence, and safety.
Run:  python3 verify/verify_design.py
"""

def gates(D, C, B, A):
    """Return the output-logic signals for count = D C B A."""
    BA   = B & A                      # AND  (7408)
    nBA  = 1 - (B | A)                # NOR  (7402)
    nDC  = 1 - (D | C)                # NOR  (7402)
    CBA  = C & BA                     # AND  (7408)
    nB   = 1 - B                      # NOT  (7404)

    MG = nDC | (C & nBA)              # Main Green  = D'C' + C B' A'
    MY = C & (A ^ B)                  # Main Yellow = C (A xor B)
    MR = D | CBA                      # Main Red    = D + CBA
    SG = (D & nB) | CBA               # Side Green  = D B' + CBA
    SY = D & B                        # Side Yellow = D B
    SR = 1 - MR                       # Side Red    = (D + CBA)'  (NOR)
    return MG, MY, MR, SG, SY, SR

def clear_n(D, C, B, A):
    """Active-low synchronous clear: NAND(D, OR(C, AND(B,A)))."""
    return 1 - (D & (C | (B & A)))

def next_count(n):
    D, C, B, A = (n >> 3) & 1, (n >> 2) & 1, (n >> 1) & 1, n & 1
    if clear_n(D, C, B, A) == 0:
        return 0
    return (n + 1) & 0xF

NAMES = ["Main Green", "Main Yellow", "Main Red", "Side Green", "Side Yellow", "Side Red"]
errors = 0

# 1) Counter sequence: must be 0..11 then wrap (MOD-12)
seq, n = [], 0
for _ in range(24):
    seq.append(n)
    n = next_count(n)
assert seq == list(range(12)) * 2, f"bad sequence {seq}"
print("Counter sequence :", seq[:12], "-> wraps to 0  (MOD-12)  OK")

# 2) Self-correction: unused states 12..15 must return to the normal cycle
for s in range(12, 16):
    assert next_count(s) == 0, f"state {s} does not recover"
print("Unused states 12-15 return to 0 on the next clock  OK")

# 3) Truth table + safety for every valid state
print("\nCount DCBA | MG MY MR | SG SY SR | Meaning")
print("-" * 62)
for n in range(12):
    D, C, B, A = (n >> 3) & 1, (n >> 2) & 1, (n >> 1) & 1, n & 1
    MG, MY, MR, SG, SY, SR = gates(D, C, B, A)
    main = (MG, MY, MR)
    side = (SG, SY, SR)
    if sum(main) != 1 or sum(side) != 1:
        errors += 1; print("ERROR: not exactly one lamp lit per road at", n)
    if (MG or MY) and (SG or SY):
        errors += 1; print("ERROR: both roads have right of way at", n)
    m = NAMES[main.index(1)]; s = NAMES[3 + side.index(1)]
    print(f"{n:>5} {D}{C}{B}{A} |  {MG}  {MY}  {MR} |  {SG}  {SY}  {SR} | {m} / {s}")

# 4) Durations
dur = {}
for n in range(12):
    D, C, B, A = (n >> 3) & 1, (n >> 2) & 1, (n >> 1) & 1, n & 1
    o = gates(D, C, B, A)
    key = (NAMES[o[:3].index(1)], NAMES[3 + o[3:].index(1)])
    dur[key] = dur.get(key, 0) + 1
print("\nDurations (clock periods):")
for k, v in dur.items():
    print(f"  {k[0]:<12}/ {k[1]:<12}: {v}")
print(f"  total cycle: {sum(dur.values())}")

print("\nRESULT:", "ALL CHECKS PASSED" if errors == 0 else f"{errors} ERROR(S)")
