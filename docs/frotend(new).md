
apps/web/
│
├── app/
│   └── (app)/
│       ├── coach/
│       │   └── [contractId]/
│       │       └── page.tsx               # [NEW-1] AI Legal Coach voice session page
│       ├── jurisdiction/
│       │   └── [contractId]/
│       │       └── page.tsx               # [NEW-2] Jurisdiction + compliance map page
│       ├── verify/
│       │   └── [contractId]/
│       │       └── page.tsx               # [NEW-3] Blockchain verification + audit trail page
│       └── finetune/
│           └── page.tsx                   # [NEW-4] Fine-tune job dashboard (admin only)
│
├── features/
│   │
│   ├── legal-coach/                       # [NEW-1] AI Legal Coach (Voice + Memory Chat)
│   │   ├── CoachPage.tsx                  # Full coach session shell
│   │   ├── VoiceOrb.tsx                   # Animated mic orb (idle / listening / speaking states)
│   │   ├── VoiceInput.tsx                 # Record button + waveform visualizer
│   │   ├── AudioPlayer.tsx                # TTS audio playback with controls
│   │   ├── CoachChatWindow.tsx            # Voice-turn transcript display (extends ChatWindow)
│   │   ├── CoachMessage.tsx               # Turn bubble with transcript + playback icon
│   │   ├── MemoryBadge.tsx                # "From your past session" memory citation badge
│   │   ├── CoachModeToggle.tsx            # Switch: Voice mode ↔ Text mode
│   │   └── NegotiationTipCard.tsx         # Inline negotiation tip surfaced by coach
│   │
│   ├── jurisdiction/                      # [NEW-2] Regional Law Intelligence
│   │   ├── JurisdictionBanner.tsx         # "Governed by: New York Law" auto-detected banner
│   │   ├── JurisdictionMap.tsx            # Visual world map with detected region highlight
│   │   ├── GoverningLawCard.tsx           # Detected law + confidence + source clause
│   │   ├── CompliancePanel.tsx            # Full compliance mapping accordion
│   │   ├── ComplianceRuleRow.tsx          # Clause → Regulation row (e.g. GDPR Art. 28)
│   │   ├── RegionalRiskFlag.tsx           # Region-specific risk flag badge
│   │   ├── JurisdictionSelector.tsx       # Manual override dropdown (if auto-detect fails)
│   │   └── RegionProfileCard.tsx          # Summary card: region name, legal system, risk level
│   │
│   ├── blockchain/                        # [NEW-3] Blockchain Verification & Audit Trail
│   │   ├── VerificationBadge.tsx          # "Verified on Polygon" trust badge (on clause cards + report)
│   │   ├── BlockchainStatusCard.tsx       # tx_hash, IPFS CID, timestamp, status (pending/confirmed)
│   │   ├── SignaturePanel.tsx             # Digital signature UI (connect wallet → sign → submit)
│   │   ├── WalletConnectButton.tsx        # MetaMask / WalletConnect button
│   │   ├── AuditTimeline.tsx              # Chronological on-chain audit event log
│   │   ├── AuditEventRow.tsx              # Single audit event: action, actor, tx_hash, time
│   │   ├── TamperAlert.tsx                # Red alert banner if hash mismatch detected
│   │   ├── IPFSLinkButton.tsx             # "View on IPFS" external link with CID
│   │   └── VerifyShareBadge.tsx           # Embeddable badge for sharing verified contracts
│   │
│   └── finetune/                          # [NEW-4] Fine-Tuning Infrastructure (Admin UI)
│       ├── FinetuneJobForm.tsx            # Launch new training job (model, dataset, LoRA config)
│       ├── FinetuneJobCard.tsx            # Job card: status, progress bar, ETA
│       ├── FinetuneJobList.tsx            # List of all jobs (running / completed / failed)
│       ├── TrainingMetricsChart.tsx       # Live loss / eval curve (Recharts)
│       ├── AdapterRegistry.tsx            # List of saved LoRA adapters + activate button
│       ├── AdapterCard.tsx                # Adapter: base model, task type, eval score
│       ├── DatasetUploader.tsx            # Upload training JSONL dataset
│       └── FinetuneConfigPanel.tsx        # LoRA hyperparams: r, alpha, epochs, lr
│
├── hooks/
│   ├── useVoiceRecorder.ts               # [NEW-1] MediaRecorder API — record, stop, get blob
│   ├── useAudioPlayback.ts               # [NEW-1] TTS audio playback state (play/pause/progress)
│   ├── useCoachSession.ts                # [NEW-1] Coach session state + memory-aware turn history
│   ├── useJurisdiction.ts                # [NEW-2] Jurisdiction fetch + manual override state
│   ├── useComplianceMap.ts               # [NEW-2] Compliance rules fetch per region
│   ├── useBlockchainVerify.ts            # [NEW-3] Verify contract, poll tx status, detect tamper
│   ├── useWallet.ts                      # [NEW-3] Wallet connection (wagmi/viem wrapper)
│   ├── useAuditTrail.ts                  # [NEW-3] Fetch on-chain audit events for a contract
│   └── useFinetuneJob.ts                 # [NEW-4] Launch job, poll status, fetch adapter list
│
├── store/
│   ├── coachStore.ts                     # [NEW-1] Voice coach session turns + memory refs + mode
│   ├── jurisdictionStore.ts              # [NEW-2] Detected jurisdiction + selected region override
│   ├── blockchainStore.ts                # [NEW-3] Verification status, tx_hash, wallet address
│   └── finetuneStore.ts                  # [NEW-4] Active jobs, adapter list, selected adapter
│
├── lib/
│   ├── audio.ts                          # [NEW-1] Audio format helpers (webm → wav, duration, waveform)
│   ├── web3.ts                           # [NEW-3] wagmi config, Polygon chain setup, contract ABIs
│   └── ipfs.ts                           # [NEW-3] IPFS gateway URL builder from CID
│
└── types/
    ├── coach.ts                          # [NEW-1] CoachTurn, CoachMemory, VoiceMode
    ├── jurisdiction.ts                   # [NEW-2] JurisdictionResult, ComplianceRule, RegionProfile
    ├── blockchain.ts                     # [NEW-3] VerifyResult, AuditEvent, WalletState
    └── finetune.ts                       # [NEW-4] FinetuneJob, AdapterConfig, TrainingMetrics
