FIX_REQUIRED

Checks:

- `unzip -t releases/pack_aa/candidates/pi_pack_aa_release_candidate_v1.zip`: PASS.
- Bundled Pack A ZIP: PASS; actual SHA-256 `58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6` matches the bundled manifest and live Pack A ZIP.
- Bundled `pack_aa/mission/MISSION_STATE.json`: `status=complete`; bundled `pack_aa/mission/REVIEW_LEDGER.json`: `final_verdict=PASS`.
- Bundled top-level demo/gate artifacts: 9 configurations; AA0–AA6 `PASS`; AA7 `PROVISIONAL_ADAPTER_REQUIRED`.

Finding:

- AA-RC-301 [release-blocking/provenance] — `PACK_AA_IMPLEMENTATION_MANIFEST.json:11-12` inside the candidate declares `/home/fabi/atlas_dihiggs/ufos/releases/pack_aa/candidates/pack_aa_release_candidate_v1.zip` with SHA-256 `cac275d8b4ceca641805e802a22b02bcb466245800fc356c37fcca620eb8492f`, but the reviewed artifact is `releases/pack_aa/candidates/pi_pack_aa_release_candidate_v1.zip` with actual SHA-256 `93deaf79a1ca2068b77d15acf5cc954b3ff3abc3af00d9d02bb36695d0c2ea04`. Reproduction: extract the candidate, read the two manifest fields, and compare `sha256sum` of the candidate ZIP. The manifest therefore does not identify the exact ZIP that passed this review; rebuild/repack the candidate after metadata regeneration and rerun the hash and integrity checks.

Sol-level reasoning required: no. Scientific, architectural, concurrency, protocol, and security reasoning were not required for this metadata/provenance finding.
