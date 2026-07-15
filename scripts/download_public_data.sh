#!/usr/bin/env bash
set -euo pipefail

source /etc/network_turbo

RAW_ROOT="${1:-/root/autodl-tmp/data/raw}"
VENV="${VENV:-/root/venv}"

download_file() {
    local url="$1"
    local destination="$2"
    local expected_sha256="$3"
    mkdir -p "$(dirname "$destination")"
    if [[ ! -f "$destination" ]]; then
        local temporary="${destination}.partial.$$"
        curl -L --fail --show-error --retry 3 --output "$temporary" "$url"
        mv "$temporary" "$destination"
    fi
    printf '%s  %s\n' "$expected_sha256" "$destination" | sha256sum -c -
}

verify_file() {
    local path="$1"
    local expected_sha256="$2"
    printf '%s  %s\n' "$expected_sha256" "$path" | sha256sum -c -
}

# CLUENER2020 official public archive.
CLUENER_ROOT="$RAW_ROOT/cluener_data"
download_file \
    "https://storage.googleapis.com/cluebenchmark/tasks/cluener_public.zip" \
    "$CLUENER_ROOT/cluener_public.zip" \
    "6dcc30e233034ecd91675182db690be187e61c5a3b5e96bf9f6b971ba8f132fa"
mkdir -p "$CLUENER_ROOT/extracted"
unzip -q -o "$CLUENER_ROOT/cluener_public.zip" -d "$CLUENER_ROOT/extracted"
verify_file "$CLUENER_ROOT/extracted/train.json" \
    "60299d202779dc84f3c3bd81f4dc08f5323d0dbf762cb50cd62dd51aa9a871f8"
verify_file "$CLUENER_ROOT/extracted/dev.json" \
    "90036b59832e007c45d11eafe5ed80549f58a18a29aaa7fe8b1229622c69ec38"
verify_file "$CLUENER_ROOT/extracted/test.json" \
    "5ca36f6fbe29230a6e3244110fcd9487fc2f5a672f5bfeba82a30f0ece72aa69"

# The upstream Few-NERD SUP link is dead. Use the pinned DFKI-SLT mirror.
FEWNERD_REVISION="205f3e9c9f3577ea2561d43f2f62dc249ab92d5b"
FEWNERD_BASE="https://huggingface.co/datasets/DFKI-SLT/few-nerd/resolve/$FEWNERD_REVISION"
FEWNERD_ROOT="$RAW_ROOT/fewnerd_data"
download_file "$FEWNERD_BASE/README.md" "$FEWNERD_ROOT/README.md" \
    "beab6f6b7887bc882b88ca7691f6e83316edde29d07fea5491a35a6ffb0cad74"
download_file "$FEWNERD_BASE/supervised/train-00000-of-00001.parquet" \
    "$FEWNERD_ROOT/supervised/train-00000-of-00001.parquet" \
    "6ccb192b1accd3d1754db2244d18ddf64040357fb5b9076a338ec421a72d7d61"
download_file "$FEWNERD_BASE/supervised/validation-00000-of-00001.parquet" \
    "$FEWNERD_ROOT/supervised/validation-00000-of-00001.parquet" \
    "d502de918f2a6510179e64bc8b7cfff4e28999188e308f8b0fe75bd71844da66"
download_file "$FEWNERD_BASE/supervised/test-00000-of-00001.parquet" \
    "$FEWNERD_ROOT/supervised/test-00000-of-00001.parquet" \
    "b7ad746fcbeb68fcc235ba7142d7c3723ea2dc39930089e947284defecf300c6"

# DuIE 2.0 official Qianyan archive, including its bundled license PDF.
DUIE_ROOT="$RAW_ROOT/duie"
download_file \
    "https://dataset-bj.cdn.bcebos.com/qianyan/DuIE_2_0.zip" \
    "$DUIE_ROOT/DuIE_2_0.zip" \
    "df223b18f3bd0fe19a61d18d7d59a22cd3f145c342c58470e93851bb4d1b40ed"
mkdir -p "$DUIE_ROOT/extracted"
unzip -q -o "$DUIE_ROOT/DuIE_2_0.zip" 'DuIE_2_0/*' -d "$DUIE_ROOT/extracted"
verify_file "$DUIE_ROOT/extracted/DuIE_2_0/train.json" \
    "3fc53f61883e313f3821e69c655e4e9ddaea5055d2431562fbc2e06dadffe415"
verify_file "$DUIE_ROOT/extracted/DuIE_2_0/dev.json" \
    "365318e952024f1910df506cc6bdcb2642d83d4b684e12ccb4685d2b6f80cd54"
verify_file "$DUIE_ROOT/extracted/DuIE_2_0/test.json" \
    "4b671ab2934ccfda225faf959c9d700e17fb157fe17d5742224de460b2ac7706"
verify_file "$DUIE_ROOT/extracted/DuIE_2_0/schema.json" \
    "9d70dc15016236a9efa27ad0c9009f6774fae2036a3dd13e962060484ba2dfd3"
verify_file "$DUIE_ROOT/extracted/DuIE_2_0/License.pdf" \
    "495bdaab78cf7104b1377f04ef65133f20539dba2bee2937d2cf9d8fc49338e0"

# CMNEE ModelScope dataset snapshot pinned to a Git revision and file hashes.
CMNEE_ROOT="$RAW_ROOT/cmnee_data"
if [[ ! -f "$CMNEE_ROOT/train.json" || ! -f "$CMNEE_ROOT/valid.json" || ! -f "$CMNEE_ROOT/test.json" ]]; then
    source "$VENV/bin/activate"
    ms download --repo-type dataset mzzzhu/CMNEE \
        --revision 5337fbd72516c3de0e67d76877778ba2d410c43e \
        --local-dir "$CMNEE_ROOT" --max-workers 4
fi
verify_file "$CMNEE_ROOT/train.json" \
    "6a796ca174eef9519e323589944859d8fa909788a4b919bbfe209612d4decad2"
verify_file "$CMNEE_ROOT/valid.json" \
    "7c907d3ace2f94b221a2d03d4deb8a0512fd85718af13edb37f103e2fd247993"
verify_file "$CMNEE_ROOT/test.json" \
    "486be178b4ce8299650261dbbb7e19fb39c79a18c977d71f020ed96c3eb80dc4"
verify_file "$CMNEE_ROOT/README.md" \
    "5eb85526c729c61dc85b7da706870d0edab4a84aa9d467f1dc4464ef9f3e6c51"
verify_file "$CMNEE_ROOT/dataset_infos.json" \
    "b7e230e9d88e7be57d0fd103dacd7d9ab017194ee4ac8c8d614a22395173f3b9"

echo "P1 public sources downloaded and hash-verified under $RAW_ROOT"
