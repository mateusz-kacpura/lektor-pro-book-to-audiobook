# Utworzenie katalogów i parzystych plików dokumentacji (EN default / PL suffix)
$basePages = @(
    "index",
    "01-architecture/c4-model/01-system-context",
    "01-architecture/c4-model/02-container-diagram",
    "01-architecture/c4-model/03-component-diagrams",
    "01-architecture/c4-model/04-deployment-topology",
    "01-architecture/clean-architecture/dependency-rule-enforcement",
    "01-architecture/clean-architecture/layer-boundaries-contracts",
    "01-architecture/clean-architecture/composition-root-ioc",
    "01-architecture/adr/adr-001-clean-architecture-type-safety",
    "01-architecture/adr/adr-002-vram-arbiter-preemption",
    "01-architecture/adr/adr-003-single-source-of-truth-filesystem",
    "01-architecture/adr/adr-004-native-vanilla-esm-ui",
    "02-domain-core/business-rules/br-001-to-005-catalog-and-slugs",
    "02-domain-core/business-rules/br-006-to-010-text-normalization-and-glossary",
    "02-domain-core/business-rules/br-011-to-015-conversion-pipeline-resilience",
    "02-domain-core/business-rules/br-016-to-020-audio-synthesis-and-caching",
    "02-domain-core/entities-and-vo/book-and-path-models",
    "02-domain-core/entities-and-vo/conversion-lifecycle-state-machine",
    "02-domain-core/entities-and-vo/audio-and-speech-specs",
    "02-domain-core/normalization-specs/go-grammar-verbalization",
    "02-domain-core/normalization-specs/polish-phonetics-and-acronyms",
    "02-domain-core/normalization-specs/numbers-dates-and-ordinals",
    "02-domain-core/normalization-specs/markdown-stripping-rules",
    "02-domain-core/validation/markdown-integrity-rules",
    "02-domain-core/validation/mermaid-syntax-contract",
    "03-application-workflows/use-cases/uc-pdf-import-and-splitting",
    "03-application-workflows/use-cases/uc-vision-ai-translation",
    "03-application-workflows/use-cases/uc-speech-synthesis-page-and-batch",
    "03-application-workflows/use-cases/uc-studio-snippet-synthesis",
    "03-application-workflows/use-cases/uc-book-context-switching",
    "03-application-workflows/ports-inventory/audio-ports-protocols",
    "03-application-workflows/ports-inventory/ocr-vision-ports-protocols",
    "03-application-workflows/ports-inventory/storage-ports-protocols",
    "03-application-workflows/ports-inventory/resource-ports-protocols",
    "03-application-workflows/ports-inventory/telemetry-ports-protocols",
    "03-application-workflows/telemetry-and-events/sse-event-stream-protocol",
    "03-application-workflows/telemetry-and-events/live-task-state-persistence",
    "04-adapters-and-interfaces/web-gui/fast-api-routing-and-dtos",
    "04-adapters-and-interfaces/web-gui/dependency-injection-state",
    "04-adapters-and-interfaces/web-gui/job-execution-thread-safety",
    "04-adapters-and-interfaces/web-gui/client-side-audio-player",
    "04-adapters-and-interfaces/web-gui/desktop-workspace-window-manager",
    "04-adapters-and-interfaces/cli/command-dispatch-and-arguments",
    "04-adapters-and-interfaces/cli/console-telemetry-reporters",
    "04-adapters-and-interfaces/ai-vision/pymupdf-renderer-adapter",
    "04-adapters-and-interfaces/ai-vision/openai-compatible-multimodal-adapter",
    "04-adapters-and-interfaces/ai-tts/universal-engine-backend-dispatch",
    "04-adapters-and-interfaces/ai-tts/content-addressable-cache-sha256",
    "04-adapters-and-interfaces/ai-tts/silero-vad-dsp-cleaner",
    "04-adapters-and-interfaces/persistence/file-system-book-repository",
    "04-adapters-and-interfaces/persistence/file-system-page-repository",
    "04-adapters-and-interfaces/persistence/studio-history-repository",
    "05-operations-and-infrastructure/vram-arbiter-runtime/mutual-exclusion-engine",
    "05-operations-and-infrastructure/vram-arbiter-runtime/llama-server-lifecycle-manager",
    "05-operations-and-infrastructure/vram-arbiter-runtime/pytorch-cuda-memory-eviction",
    "05-operations-and-infrastructure/ai-models-catalog/vision-models-spec-gemma-qwen",
    "05-operations-and-infrastructure/ai-models-catalog/tts-models-spec-omnivoice-chatterbox",
    "05-operations-and-infrastructure/diagnostics-and-benchmarking/memory-leak-profiling-protocol",
    "05-operations-and-infrastructure/diagnostics-and-benchmarking/heap-and-working-set-thresholds",
    "05-operations-and-infrastructure/diagnostics-and-benchmarking/gpu-telemetry-adapter",
    "05-operations-and-infrastructure/runbooks/vram-oom-recovery",
    "05-operations-and-infrastructure/runbooks/orphaned-process-cleanup",
    "05-operations-and-infrastructure/runbooks/environment-configuration-env",
    "06-quality-and-engineering/type-system/zero-any-policy",
    "06-quality-and-engineering/type-system/newtype-strong-identifiers",
    "06-quality-and-engineering/type-system/mypy-strict-enforcement",
    "06-quality-and-engineering/test-pyramid/unit-domain-isolation",
    "06-quality-and-engineering/test-pyramid/unit-application-fakes",
    "06-quality-and-engineering/test-pyramid/integration-adapters",
    "06-quality-and-engineering/test-pyramid/e2e-blackbox-workflows",
    "06-quality-and-engineering/test-pyramid/benchmark-regression-testing"
)

$createdDirs = 0
$createdFiles = 0

foreach ($base in $basePages) {
    $enPath = "docs/$base.md"
    $plPath = "docs/$base.pl.md"
    
    $dir = Split-Path -Parent $enPath
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        $createdDirs++
    }

    $titleName = (Split-Path -Leaf $base).Replace("-", " ").ToUpper()

    # 1. Wersja angielska (Domyślna)
    if (-not (Test-Path $enPath)) {
        @"
# $titleName

*Status: In development / Technical specification*

Document content under drafting.
"@ | Out-File -FilePath $enPath -Encoding utf8
        $createdFiles++
    }

    # 2. Wersja polska (Suffix .pl.md)
    if (-not (Test-Path $plPath)) {
        @"
# $titleName

*Status: W przygotowaniu / Specyfikacja techniczna*

Treść dokumentu w trakcie redagowania.
"@ | Out-File -FilePath $plPath -Encoding utf8
        $createdFiles++
    }
}

Write-Host "Pomyślnie wygenerowano strukturę dwujęzyczną." -ForegroundColor Green
Write-Host "Utworzone/zweryfikowane pliki: $($basePages.Count * 2) (EN: $($basePages.Count), PL: $($basePages.Count))" -ForegroundColor Cyan