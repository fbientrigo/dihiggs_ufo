# Generator-closure consolidation

Canonical run: `results/generator_closure/20260801T000013Z/`

The clean registered Pack AA worktree at `4f4009246d7798936d9656558879cb0f84d17940` was used. The study inventories 100-event stable-H2 MadGraph LHE, the derived 1000-event repeated LHE, matched auxiliary Pythia D0/D1 truth, and nine canonical Pack AA truth samples. No HepMC/FastJet jet sample exists.

The result is `GENERATOR_CLOSURE_VALIDATED_WITH_EXPECTED_SHOWER_EFFECTS`. H2 decay four-momentum closes within the predeclared `1e-6 GeV` component tolerance. Canonical Pythia recoil changes H2 pT and angular observables as expected from shower/event-record recoil; H2H2 mass and H2-to-direct-daughter parent reconstruction close. The 4gamma result is explicitly parent-reconstruction closure, not MG four-photon agreement.

`bb` is `NOT_COMPARABLE` because MG has no b partons and the available canonical bb truth schema lacks daughter four-vectors. Jets are `UNKNOWN` because no reconstructed jet input or FastJet installation is available. No source samples or excluded repositories were modified.
