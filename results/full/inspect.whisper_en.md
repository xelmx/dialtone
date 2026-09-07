normaliser: `whisper_en`

| model | condition | n | changed vs clean | with errors | right→wrong | wrong→right |
|---|---|---:|---:|---:|---:|---:|
| whisper-turbo | clean | 2620 | 0 | 600 | 0 | 0 |
| whisper-turbo | g711u | 2620 | 253 | 610 | 70 | 60 |
| whisper-turbo | pots | 2620 | 294 | 642 | 101 | 59 |
| parakeet-tdt-0.6b-v3 | clean | 2620 | 0 | 625 | 0 | 0 |
| parakeet-tdt-0.6b-v3 | g711u | 2620 | 217 | 638 | 58 | 45 |
| parakeet-tdt-0.6b-v3 | pots | 2620 | 268 | 643 | 76 | 58 |
| qwen3-asr-0.6b | clean | 2620 | 0 | 666 | 0 | 0 |
| qwen3-asr-0.6b | g711u | 2620 | 185 | 688 | 50 | 28 |
| qwen3-asr-0.6b | pots | 2620 | 276 | 729 | 99 | 36 |

**Utterances every model gets wrong on clean audio: 419 of 2620** (16.0%) — reference/normaliser artefacts, the floor under the numbers.
- `1089-134691-0005` ref: whose feet are as the feet of harts and underneath the everlasting arms
- `1089-134691-0010` ref: brother mac ardle brother keogh
- `1089-134691-0014` ref: the phrase and the day and the scene harmonized in a chord
- `1089-134691-0017` ref: the europe they had come from lay out there beyond the irish sea europe of strange tongues and valleyed and woodbegirt a
- `1089-134691-0024` ref: stephanos dedalos

**whisper-turbo — correct on clean, wrong on `pots` (4 shown)**
- `1284-134647-0005`
  - ref: they asserted with confidence and almost with exultation that the apostolical succession was interrupted that all the bishops of europe and 
  - pots: they asserted with confidence and almost with exultation that the apostolical succession was interrupted that all the bishops of europe and 
- `3729-6852-0045`
  - ref: he had a good appetite could tell a good story without laughing was celebrated for his witty repartees and his sociable manners but he spent
  - pots: he had a good appetite could tell a good story without laughing was celebrated for his witty repartees and his sociable manners but he spent
- `1188-133604-0002`
  - ref: by being studious of color they are studious of division and while the chiaroscurist devotes himself to the representation of degrees of for
  - pots: by being studious of color they are studious of division and while the chiaroscurist devotes himself to the representation of degrees of for
- `3575-170457-0026`
  - ref: p s pray sir excuse me for writing to you a 2nd time i could not help writing partly to tell you how thankful i am for your kindness and par
  - pots: p s pray sir excuse me for writing to you a 2nd time i cannot help writing partly to tell you how thankful i am for your kindness and partly

**parakeet-tdt-0.6b-v3 — correct on clean, wrong on `pots` (4 shown)**
- `121-127105-0006`
  - ref: the others resented postponement but it was just his scruples that charmed me
  - pots: the others resented postponement but it was just her scruples that charmed me
- `121-127105-0020`
  - ref: who was it she was in love with the story will tell i took upon myself to reply 0 i can not wait for the story the story will not tell said 
  - pots: who was it she was in love with the story will tell i took upon myself to reply 0 i can not wait for the story the story will not tell said 
- `1221-135767-0019`
  - ref: mother cried she i see you here look look
  - pots: mother cried she i see you here look
- `1284-1181-0017`
  - ref: the wizard of oz who used to be a humbug and knew no magic at all has been taking lessons of glinda and i am told he is getting to be a pret
  - pots: the wizard of oz who used to be a humbug and knew no magic at all has been taking lessons of glinda and i am told he is getting to be a pret

**qwen3-asr-0.6b — correct on clean, wrong on `pots` (4 shown)**
- `4970-29093-0006`
  - ref: law seemed to him well enough as a science but he never could discover a practical case where it appeared to him worth while to go to law an
  - pots: law seemed to him well enough as a science but he never could discover a practical case where it appeared to him worthwhile to go to law and
- `260-123288-0015`
  - ref: from the under surface of the clouds there are continual emissions of lurid light electric matter is in continual evolution from their compo
  - pots: from the undersurface of the clouds there are continual emissions of lurid light electric matter is in continual evolution from their compon
- `2300-131720-0017`
  - ref: edison had installed his historic 1st great central station system in new york on the multiple arc system covered by his feeder and main inv
  - pots: anderson had installed his historic 1st great central station system in new york on the multiple arc system covered by his feeder and main i
- `7729-102255-0003`
  - ref: for general service therefore requiring no special effort the numerical strength of the factions was about equal while on extraordinary occa
  - pots: for general service therefore requiring no special effort the numerical strength of the factions was about equal while on extraordinary occa
