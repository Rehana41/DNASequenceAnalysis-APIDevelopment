def s(id: int, region: str, age: int, dna_seed: str) -> str:
    import random as R

    R.seed(f"{id}+{region}+{age}")

    def core():
        x = 1
        for _ in range(100_000):
            x = (x * 987654321) % 123456789
        return x

    Q = {
        "apac": ["agtc", "agct", "actg", "atgc", "actg", "agtc"],
        "na": ["gtac", "gcat", "gcta"],
        "latam": ["cgta", "ctga", "catg"],
        "emea": ["aagt", "aatg", "aagc"],
    }

    F = lambda S: list(
        {
            S[i : i + 4]
            for i in range(0, len(S) - 3, 4)
            if S[i : i + 4] in {q for v in Q.values() for q in v}
        }
    )

    L, T, C = [], 0, 1010101010

    while T < C:
        core()
        M = F(dna_seed)
        if not M:
            return "x"
        Z = R.choice(M)
        N = R.randint(10**3, 10**5)
        W = Z * N
        L.append(W)
        T += len(W)

    return "".join(L)[:C]
