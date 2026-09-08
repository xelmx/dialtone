normaliser: `whisper_en`

| model | condition | n | changed vs clean | with errors | right→wrong | wrong→right |
|---|---|---:|---:|---:|---:|---:|
| parakeet-tdt-0.6b-v3 | babble10 | 2620 | 787 | 983 | 427 | 69 |
| parakeet-tdt-0.6b-v3 | clean | 2620 | 0 | 625 | 0 | 0 |
| parakeet-tdt-0.6b-v3 | g711u | 2620 | 217 | 638 | 58 | 45 |
| parakeet-tdt-0.6b-v3 | opus12 | 2620 | 202 | 633 | 52 | 44 |
| parakeet-tdt-0.6b-v3 | opus8 | 2620 | 385 | 697 | 141 | 69 |
| parakeet-tdt-0.6b-v3 | pink10 | 2620 | 459 | 748 | 192 | 69 |
| parakeet-tdt-0.6b-v3 | pots | 2620 | 268 | 643 | 76 | 58 |
| parakeet-tdt-0.6b-v3 | pots_babble10 | 2620 | 1080 | 1229 | 655 | 51 |
| qwen3-asr-0.6b | babble10 | 2620 | 693 | 986 | 360 | 40 |
| qwen3-asr-0.6b | clean | 2620 | 0 | 666 | 0 | 0 |
| qwen3-asr-0.6b | g711u | 2620 | 185 | 688 | 50 | 28 |
| qwen3-asr-0.6b | opus12 | 2620 | 208 | 683 | 53 | 36 |
| qwen3-asr-0.6b | opus8 | 2620 | 366 | 766 | 139 | 39 |
| qwen3-asr-0.6b | pink10 | 2620 | 372 | 783 | 155 | 38 |
| qwen3-asr-0.6b | pots | 2620 | 276 | 729 | 99 | 36 |
| qwen3-asr-0.6b | pots_babble10 | 2620 | 1081 | 1276 | 637 | 27 |
| whisper-turbo | babble10 | 2620 | 671 | 923 | 365 | 42 |
| whisper-turbo | clean | 2620 | 0 | 600 | 0 | 0 |
| whisper-turbo | g711u | 2620 | 252 | 610 | 70 | 60 |
| whisper-turbo | opus12 | 2620 | 222 | 621 | 66 | 45 |
| whisper-turbo | opus8 | 2620 | 352 | 678 | 133 | 55 |
| whisper-turbo | pink10 | 2620 | 375 | 724 | 162 | 38 |
| whisper-turbo | pots | 2620 | 293 | 642 | 101 | 59 |
| whisper-turbo | pots_babble10 | 2620 | 1127 | 1291 | 727 | 36 |

**Utterances every model gets wrong on clean audio: 419 of 2620** (16.0%) — reference/normaliser artefacts, the floor under the numbers.
- `1089-134691-0005` ref: whose feet are as the feet of harts and underneath the everlasting arms
- `1089-134691-0010` ref: brother mac ardle brother keogh
- `1089-134691-0014` ref: the phrase and the day and the scene harmonized in a chord
- `1089-134691-0017` ref: the europe they had come from lay out there beyond the irish sea europe of strange tongues and valleyed and woodbegirt a
- `1089-134691-0024` ref: stephanos dedalos

**parakeet-tdt-0.6b-v3 — correct on clean, wrong on `pots_babble10` (8 shown)**
- `1089-134686-0000`
  - ref: he hoped there would be stew for dinner turnips and carrots and bruised potatoes and fat mutton pieces to be ladled out in thick peppered fl
  - pots_babble10: he hoped there would be stew for dinner turnips and carrots and bruised potatoes and fat mutton pieces to be ladled out in thick peppered fl
- `1089-134686-0002`
  - ref: after early nightfall the yellow lamps would light up here and there the squalid quarter of the brothels
  - pots_babble10: after early nightfall the yellow lamps would light up here and there in the squalid quarter of the brothel
- `1089-134686-0015`
  - ref: but the dusk deepening in the schoolroom covered over his thoughts the bell rang
  - pots_babble10: but the dust deepening in the schoolroom hovered over his thoughts the bell rang
- `1089-134686-0021`
  - ref: if a layman in giving baptism pour the water before saying the words is the child baptized
  - pots_babble10: if a layman in giving baptism poured water before saying the word is the child baptized
- `1089-134686-0035`
  - ref: he had the faith in him that moves mountains
  - pots_babble10: he has a faith in him that moves mountains
- `1089-134691-0013`
  - ref: idle and embittering finally to argue against his own dispassionate certitude that the commandment of love bade us not to love our neighbor 
  - pots_babble10: idle and embittering finally to argue against his own dispassionate certitude that the commandment of love made us not to love our neighbor 
- `1089-134691-0015`
  - ref: words was it their colors
  - pots_babble10: word was it their colors
- `1089-134691-0018`
  - ref: again again
  - pots_babble10: again

**qwen3-asr-0.6b — correct on clean, wrong on `pots_babble10` (8 shown)**
- `4507-16021-0026`
  - ref: to keep afloat and to rescue from oblivion to hold above the gulf were it but a fragment of some language which man has spoken and which wou
  - pots_babble10: to keep afloat and to rescue from oblivion to hold above the goal where it but a fragment of some language which man has spoken and which wo
- `672-122797-0008`
  - ref: this happened every year and the young fir tree that had now grown to a very comely size trembled at the sight for the magnificent great tre
  - pots_babble10: this happened every year and the young fir tree that had now grown to a very comely size trembled at the sight for the magnificent great tre
- `4970-29093-0006`
  - ref: law seemed to him well enough as a science but he never could discover a practical case where it appeared to him worth while to go to law an
  - pots_babble10: law seemed to him well enough as a science but he never could discover a practical case where it appeared to him worthwhile to go to law and
- `5105-28241-0015`
  - ref: to the surprise of all and especially of lieutenant procope the line indicated a bottom at a nearly uniform depth of from 4 to 5 fathoms and
  - pots_babble10: to the surprise of all and especially of lieutenant procope the line indicated a bottom at a nearly uniform depth of from 4 to 5 fathoms and
- `3729-6852-0033`
  - ref: you are now in the only country in the world where wit can make a fortune by selling either a genuine or a false article in the 1st case it 
  - pots_babble10: you are now in the only country in the world where witch can make a fortune by selling either a genuine or a false article in the 1st case i
- `5639-40744-0031`
  - ref: so persuasive were her entreaties and so strong her assurances that no harm whatever could result to them from the information she sought th
  - pots_babble10: so persuasive were her entreaties and so strong her assurances that no harm whatever could result to them from the information she sought th
- `2300-131720-0028`
  - ref: there was infinite skepticism around him on the subject and while other inventors were also giving the subject their thought the public took
  - pots_babble10: there was instant skepticism around him on the subject and while other inventors were also giving the subject their thoughts the public took
- `2300-131720-0035`
  - ref: in this connection it should be mentioned that the association of edison illuminating companies in the same year adopted resolutions unanimo
  - pots_babble10: in this connection it should be mentioned that the association of edison illuminating companies in the same year adopted resolutions unanimo

**whisper-turbo — correct on clean, wrong on `pots_babble10` (8 shown)**
- `2094-142345-0008`
  - ref: but there is always a stronger sense of life when the sun is brilliant after rain and now he is pouring down his beams and making sparkles a
  - pots_babble10: but there is always a stronger sense of life when the sun is brilliant after rain and now he is pouring down his beans and making sparkles a
- `672-122797-0008`
  - ref: this happened every year and the young fir tree that had now grown to a very comely size trembled at the sight for the magnificent great tre
  - pots_babble10: this happened every year and the young fir tree that had now grown to a very comely size trembled at the sight for the magnificent great tre
- `4970-29093-0006`
  - ref: law seemed to him well enough as a science but he never could discover a practical case where it appeared to him worth while to go to law an
  - pots_babble10: law seemed to him well enough as a science but he never could discover a practical case where it appeared to him worthwhile to go to law and
- `3729-6852-0033`
  - ref: you are now in the only country in the world where wit can make a fortune by selling either a genuine or a false article in the 1st case it 
  - pots_babble10: you are now in the only country in the world where witch can make a fortune by selling either a genuine or a false article in the 1st case i
- `5639-40744-0031`
  - ref: so persuasive were her entreaties and so strong her assurances that no harm whatever could result to them from the information she sought th
  - pots_babble10: so persuasive were her entreatment and so strong her assurances that no harm whatever could result to them from the information she sought t
- `3575-170457-0036`
  - ref: my eyes fill with tears when i contrast the bliss of such a state brightened by hopes of the future with the melancholy state i now live in 
  - pots_babble10: my eyes fill with tears when i contrast the bliss of such a state brightened by hopes of the future with the melancholy state i now live in 
- `4507-16021-0032`
  - ref: he must descend with his heart full of charity and severity at the same time as a brother and as a judge to those impenetrable casemates whe
  - pots_babble10: he must defend with his heart full of charity and severity at the same time as a brother and as a judge to those impenetrable tastemates for
- `2961-960-0000`
  - ref: he passes abruptly from persons to ideas and numbers and from ideas and numbers to persons from the heavens to man from astronomy to physiol
  - pots_babble10: he passes abruptly from persons to ideas and numbers and from ideas and numbers to persons from the heavens to man from astronomy to physiol
