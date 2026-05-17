
# New Backend Additions — 4 Feature Modules

## Feature 1: AI Legal Coach (Voice + Memory-Aware Chat)
## Feature 2: Regional Law Intelligence (Jurisdiction-Aware Analysis)
## Feature 3: Blockchain Verification & Audit Trail (Polygon + IPFS)
## Feature 4: Legal Model Fine-Tuning Infrastructure (QLoRA/Unsloth)

---

services/api/
│
├── app/
│   │
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           ├── voice.py                     # [NEW-1] POST /voice/transcribe, POST /voice/synthesize
│   │           ├── legal_coach.py               # [NEW-1] POST /coach/{contractId} — voice-aware coaching session
│   │           ├── jurisdiction.py              # [NEW-2] GET /jurisdiction/{contractId} — governing law + compliance
│   │           ├── compliance.py                # [NEW-2] GET /compliance/{contractId}/{region} — regional risk map
│   │           ├── blockchain.py                # [NEW-3] POST /verify, GET /verify/{contractId}, POST /sign
│   │           └── finetune.py                  # [NEW-4] POST /finetune/job, GET /finetune/job/{jobId}
│   │
│   ├── models/
│   │   ├── coaching_session.py                  # [NEW-1] CoachingSession (voice turns, memory refs)
│   │   ├── voice_turn.py                        # [NEW-1] VoiceTurn (transcript, tts_audio_ref, role)
│   │   ├── jurisdiction_profile.py              # [NEW-2] JurisdictionProfile (detected law, region, flags)
│   │   ├── compliance_mapping.py                # [NEW-2] ComplianceMapping (clause → regulation cross-ref)
│   │   ├── blockchain_record.py                 # [NEW-3] BlockchainRecord (tx_hash, ipfs_cid, sig, status)
│   │   ├── audit_event.py                       # [NEW-3] AuditEvent (on-chain log entry per contract action)
│   │   └── finetune_job.py                      # [NEW-4] FinetuneJob (status, base_model, adapter_path)
│   │
│   ├── schemas/
│   │   ├── voice.py                             # [NEW-1] VoiceTranscribeRequest/Response, TTSRequest/Response
│   │   ├── legal_coach.py                       # [NEW-1] CoachTurnRequest, CoachTurnResponse, CoachMemory
│   │   ├── jurisdiction.py                      # [NEW-2] JurisdictionResult, GoverningLawDetection
│   │   ├── compliance.py                        # [NEW-2] ComplianceMapResult, RegionalRiskFlag
│   │   ├── blockchain.py                        # [NEW-3] VerifyRequest, VerifyResult, SignaturePayload, AuditLog
│   │   └── finetune.py                          # [NEW-4] FinetuneJobCreate, FinetuneJobStatus, AdapterConfig
│   │
│   ├── services/
│   │   ├── voice_service.py                     # [NEW-1] STT (Deepgram/Whisper) + TTS (ElevenLabs/Polly) orchestration
│   │   ├── legal_coach_service.py               # [NEW-1] Memory-aware coaching: retrieves past turns, calls Claude
│   │   ├── jurisdiction_service.py              # [NEW-2] Governing law extraction + region classifier
│   │   ├── compliance_service.py                # [NEW-2] Clause → regulation mapper per jurisdiction
│   │   ├── blockchain_service.py                # [NEW-3] Polygon tx submission, IPFS pin, sig verification
│   │   ├── audit_service.py                     # [NEW-3] On-chain audit event logger + retriever
│   │   └── finetune_service.py                  # [NEW-4] QLoRA job launcher, status poller, adapter registry
│   │
│   ├── repositories/
│   │   ├── coaching_session_repo.py             # [NEW-1]
│   │   ├── jurisdiction_repo.py                 # [NEW-2]
│   │   ├── blockchain_repo.py                   # [NEW-3]
│   │   └── finetune_repo.py                     # [NEW-4]
│   │
│   ├── workers/
│   │   └── tasks.py                             # [UPDATED] + finetune_job task, blockchain_submit task
│   │
│   └── utils/
│       ├── audio_handler.py                     # [NEW-1] Audio upload temp storage, format conversion (webm→wav)
│       ├── web3_client.py                       # [NEW-3] Web3.py Polygon RPC client wrapper
│       ├── ipfs_client.py                       # [NEW-3] IPFS/Pinata HTTP client wrapper
│       └── adapter_loader.py                    # [NEW-4] Load/unload LoRA adapters from disk into inference
│
├── finetune/                                    # [NEW-4] Standalone fine-tuning pipeline (runs on GPU worker)
│   ├── README.md
│   ├── train.py                                 # QLoRA training entry point (Unsloth + TRL SFTTrainer)
│   ├── config.py                                # Pydantic training config (model_id, lora_r, epochs, etc.)
│   ├── dataset.py                               # Dataset loader + formatter (legal clause → instruction format)
│   ├── evaluate.py                              # Eval loop (ROUGE, legal-specific metrics)
│   ├── export.py                                # Merge adapter → full model, GGUF export optional
│   ├── push.py                                  # Push adapter to HuggingFace Hub or local registry
│   └── data/
│       ├── raw/                                 # Raw legal corpora (contracts, case law, statutes)
│       ├── processed/                           # Formatted JSONL instruction datasets
│       └── splits/
│           ├── train.jsonl
│           ├── val.jsonl
│           └── test.jsonl
│
├── blockchain/                                  # [NEW-3] Smart contracts + ABI
│   ├── contracts/
│   │   ├── ContractRegistry.sol                 # Stores contract hash + metadata on-chain
│   │   └── AuditLogger.sol                      # Emits on-chain audit events per action
│   ├── abi/
│   │   ├── ContractRegistry.json
│   │   └── AuditLogger.json
│   ├── scripts/
│   │   ├── deploy.py                            # Hardhat/Brownie deploy script
│   │   └── verify_contract.py                  # Polygonscan verification helper
│   └── hardhat.config.js
│
├── jurisdiction_data/                           # [NEW-2] Static + scraped regional law reference data
│   ├── governing_law_patterns.json             # Regex/NLP patterns for law detection (e.g. "governed by laws of NY")
│   ├── region_profiles/
│   │   ├── us/
│   │   │   ├── federal.json                    # Federal contract law refs
│   │   │   ├── california.json
│   │   │   ├── new_york.json
│   │   │   └── texas.json
│   │   ├── eu/
│   │   │   ├── gdpr.json
│   │   │   ├── germany.json
│   │   │   └── france.json
│   │   ├── uk/
│   │   │   └── england_wales.json
│   │   └── in/
│   │       ├── indian_contract_act.json
│   │       └── it_act.json
│   └── compliance_rules.json                   # Clause-type → regulation cross-reference index
│
├── voice/                                       # [NEW-1] Voice config + prompt assets
│   ├── stt_config.json                          # STT provider config (Deepgram model, language hints)
│   ├── tts_config.json                          # TTS provider config (voice_id, speed, format)
│   └── coach_prompts/
│       ├── system_prompt.txt                    # Legal coach system prompt (memory-injection template)
│       ├── negotiation_guide.txt               # Negotiation coaching persona prompt
│       └── explanation_guide.txt              # Plain-language clause explanation prompt
│
├── migrations/
│   └── versions/
│       ├── 002_voice_coaching.py               # [NEW-1] coaching_sessions, voice_turns tables
│       ├── 003_jurisdiction.py                 # [NEW-2] jurisdiction_profiles, compliance_mappings tables
│       ├── 004_blockchain.py                   # [NEW-3] blockchain_records, audit_events tables
│       └── 005_finetune.py                     # [NEW-4] finetune_jobs table
│
└── tests/
    ├── unit/
    │   ├── test_voice_service.py               # [NEW-1]
    │   ├── test_jurisdiction_service.py        # [NEW-2]
    │   ├── test_blockchain_service.py          # [NEW-3]
    │   └── test_finetune_service.py            # [NEW-4]
    └── integration/
        ├── test_voice_api.py                   # [NEW-1]
        ├── test_jurisdiction_api.py            # [NEW-2]
        ├── test_blockchain_api.py              # [NEW-3]
        └── test_finetune_api.py                # [NEW-4]
