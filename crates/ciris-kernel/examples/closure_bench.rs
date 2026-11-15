//! The closure at the sizes persist's own benches use (`benches/scores_read.rs`: 256 to 16,000 rows), and
//! 64,000. Compares the eager closure the crate first shipped with the lazy one, on two shapes of graph.
//!
//!     cargo run --release --example closure_bench
#[path = "../tests/common/dag.rs"]
mod dag;
#[path = "../tests/common/eager.rs"]
mod eager;

use ciris_kernel::graph::Graph;
use dag::{dag, Lcg};
use std::time::Instant;

fn ms(t: Instant) -> f64 {
    t.elapsed().as_secs_f64() * 1e3
}

fn main() {
    println!("shape     rows   | eager build  queries | lazy build  queries  one past  every past");
    for (shape, k, w) in [("narrow", 2u32, 8u32), ("wide", 3, 4096)] {
        for n in [256u32, 1_024, 4_096, 16_000, 64_000] {
            let rows = dag(n, k, w, 7);
            let m = rows.len();
            let pairs: Vec<(usize, usize)> = {
                let mut g = Lcg(9);
                (0..10_000).map(|_| ((g.next() as usize) % m, (g.next() as usize) % m)).collect()
            };
            let big = std::env::var("BENCH_EAGER_ALL").is_ok();
            let (eb, eq) = if n <= 16_000 || big {
                let t = Instant::now();
                let e = eager::EagerGraph::new(rows.iter());
                let b = ms(t);
                let t = Instant::now();
                let c = pairs.iter().filter(|&&(a, b)| e.concurrent(a, b)).count();
                std::hint::black_box(c);
                (format!("{b:10.1}"), format!("{:8.2}", ms(t)))
            } else {
                ("         -".into(), "       -".into())
            };
            let t = Instant::now();
            let l = Graph::new(rows.iter());
            let lb = ms(t);
            let t = Instant::now();
            let c = pairs.iter().filter(|&&(a, b)| l.concurrent(a, b)).count();
            std::hint::black_box(c);
            let lq = ms(t);
            let t = Instant::now();
            std::hint::black_box(Graph::new(rows.iter()).depth(m - 1));
            let one = ms(t);
            let every = if n <= 16_000 || big {
                let t = Instant::now();
                let g = Graph::new(rows.iter());
                let s: usize = (0..m).map(|i| g.ancestors(i).len()).sum();
                std::hint::black_box(s);
                format!("{:10.1}", ms(t))
            } else {
                "         -".into()
            };
            println!("{shape:8} {n:6}   | {eb} {eq} | {lb:10.2} {lq:8.2} {one:9.2} {every}   (ms)");
        }
    }
}
