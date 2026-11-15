//! Generated row graphs for the closure's oracle test and the benchmark: each row names up to `k` rows
//! drawn from a window of earlier ones, by a fixed linear congruential generator, so every run is the same.
#![allow(dead_code)]
use ciris_kernel::Row;

#[derive(Clone, Debug, PartialEq)]
pub struct N {
    pub id: u32,
    pub names: Vec<u32>,
    pub signer: u32,
}

impl Row for N {
    type Id = u32;
    type Key = u32;
    fn id(&self) -> &u32 {
        &self.id
    }
    fn names(&self) -> &[u32] {
        &self.names
    }
    fn signer(&self) -> &u32 {
        &self.signer
    }
}

pub struct Lcg(pub u64);
impl Lcg {
    pub fn next(&mut self) -> u64 {
        self.0 = self.0.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        self.0 >> 33
    }
}

/// `n` rows; row i names up to `k` of the `window` rows before it (a chain when k = 1, window = 1).
pub fn dag(n: u32, k: u32, window: u32, seed: u64) -> Vec<N> {
    let mut g = Lcg(seed);
    (0..n)
        .map(|i| {
            let m = if i == 0 { 0 } else { 1 + (g.next() as u32) % k };
            let names = (0..m).map(|_| i - 1 - (g.next() as u32) % i.min(window)).collect();
            N { id: i, names, signer: (g.next() % 16) as u32 }
        })
        .collect()
}
