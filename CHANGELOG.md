## Change Log

### 0.9.0 (2022/04/20 10:30 +00:00)
- [dd5fb04](https://github.com/spotify/cstar/commit/dd5fb04b71e9d219953d3f0f7532f8145f499ea0) add sudo option (@eedgar)
- [865f069](https://github.com/spotify/cstar/commit/865f06908739e6baccacaf9de4e1496b6d73160b) parse ipv6 tokens properly (@eedgar)
- [f0e92c8](https://github.com/spotify/cstar/commit/f0e92c8212d0f67448eb221a5526f199c33c4c5c) Bump paramiko (@yakirgb)
- [6172580](https://github.com/spotify/cstar/commit/6172580a3ceba091f9599df355c267f9ce22a99a) Add --jmx-passwordfile cli argument (@xtimon)
- [8ccc437](https://github.com/spotify/cstar/commit/8ccc43761ad1d57001147d1a87ae8d2507344177) Correctly process --hosts-variables argument (@smarsching)

### 0.8.1 (2020/12/04 09:00 +00:00)
- [a9bbc3d](https://github.com/spotify/cstar/commit/a9bbc3d8c8bed7d7b76d78358ee856b0805179a1) Fix error when continuing a job with the cache (@adejanovski)
- [e7232d2](https://github.com/spotify/cstar/commit/e7232d28b0b938a50b8300aa89c1e4e177d0b8e3) Fix missing host_variables on resuming jobs with running hosts (@adejanovski)
- [5374ac8](https://github.com/spotify/cstar/commit/5374ac8648433cc2a59b212735507e5d460acae2) Fix regex for rack string to include dashes (@ivanmp91)
- [185e4b6](https://github.com/spotify/cstar/commit/185e4b6b80e1910ae78769eb84fe6fdd091a413c) Update regex (@ivanmp91)
- [331409d](https://github.com/spotify/cstar/commit/331409dd8d271a9395dffc165f94fd7f1f3dfe2f) Add host specific variables (@adejanovski)
- [8719458](https://github.com/spotify/cstar/commit/8719458f80628a6eac1b09ebc9afb0261159d5cd) fix jobreader variable naming (@adejanovski)
- [9091b6c](https://github.com/spotify/cstar/commit/9091b6c026b6ac402297b0801916540ae709dd49) Add integration tests (@adejanovski)
- [a466694](https://github.com/spotify/cstar/commit/a4666941f3731d4a44e21b352b36acf5f12eebb9) Create a docker-compose setup that creates a Cassandra cluster with sshd, to run the cstar integration tests in. (@michaelsembwever)

### 0.8.0 (2020/05/20 12:19 +00:00)
- [c545395](https://github.com/spotify/cstar/commit/c545395d4e19cae12939a51a5ac57e9dc3ec1ced) Paramiko sometimes hangs if the buffer is too big. (@npeshek-spotx)
- [e95a0e7](https://github.com/spotify/cstar/commit/e95a0e740f2b9c86dd27e3f4d96393b780707a83) Remove code duplication of #40 (@rzvoncek)
- [bf50981](https://github.com/spotify/cstar/commit/bf509816d4282721cd0603e5482dbfeef9412ad0) Update paramiko to 2.7.1
- [8dba321](https://github.com/spotify/cstar/commit/8dba32147a4448c27eaae2e396d288736e7690e8) Enable ssh keepalive to avoid "broken pipe" errors for long-running commands
- [fd4cfdc](https://github.com/spotify/cstar/commit/fd4cfdcaaa7d8594a212bd42e4852e8dd2af3b05) Improve performance of "Preheating DNS cache" phase when running against clusters with vnodes enabled
- [3a8dd81](https://github.com/spotify/cstar/commit/3a8dd8185dca04041c30cb859254d3fc9d69fc32) Cache the topology and the endpoint mappings to speed up cstar on subsequent calls (@adejanovski)
- [5967ff8](https://github.com/spotify/cstar/commit/5967ff8797c45cad41bdb5273a119f670225cee1) Add shortcuts for strategy+dc-parallel (ie --one or --topology-per-dc) (@arodrime)
- [ec80539](https://github.com/spotify/cstar/commit/ec805393670c1701657cfb6984919be7783659c1) fix error where the traceback doesnt work (@eedgar)
- [d72bb9e](https://github.com/spotify/cstar/commit/d72bb9e874512c97d53ecfdc9c68c0d5c81fefd0) Update cstarcli.py (@rjablonovsky)
- [9811c44](https://github.com/spotify/cstar/commit/9811c44ea74f0b7826eccec60a47210570d74ee5) Store & pass dc_filter when resuming jobs (@arodrime)
- [3938a95](https://github.com/spotify/cstar/commit/3938a95fa3b30716cc249d102d898311c42d6a56) Fix multiple clusters running with strategy=topology (@arodrime)
- [f749b36](https://github.com/spotify/cstar/commit/f749b3612ab1b4b10498c74f148a47df6fb49e0d) dc-serial always is default, 'one' strategy now considers dc-parallel flag (@arodrime)
- [6ff4d90](https://github.com/spotify/cstar/commit/6ff4d90b2da215546a89bb4c70333e5ebe840add) remove the ssh2-python remote runner (@michaelsembwever)
- [2f2145c](https://github.com/spotify/cstar/commit/2f2145c84eb9c09df7bb9296e41b1b8b5209fb73) Fix failing tests after the addition of jmx authentication support (@adejanovski)
- [b4016e3](https://github.com/spotify/cstar/commit/b4016e39a942daae208178bf74429ae4193a7436) add support for JMX authentication

### 0.7.3 (2018/10/25 14:17 +00:00)
- [8714730](https://github.com/spotify/cstar/commit/871473059071a5764be5ba4bc74a373508e7b84a) Revert default ssh lib to paramiko as ssh2 cannot handle sudo commands (@adejanovski)
- [f038ac2](https://github.com/spotify/cstar/commit/f038ac2a6e11c23478d034360026a1e6e1080477) Add the ability to pass forcefully set the job id. (@adejanovski)

### 0.7.2 (2018/10/11 16:25 +00:00)
- [#27](https://github.com/spotify/cstar/pull/27) ssh2-python by default and scp instead of sftp (@adejanovski)
- [#28](https://github.com/spotify/cstar/pull/28) paramiko==2.3.3 (@spotify)
- [6c3e347](https://github.com/spotify/cstar/commit/6c3e347ab99443c8a298558936ed13feb45a7e99) paramiko==2.3.3 (@Bj0rnen)
- [ceb5be2](https://github.com/spotify/cstar/commit/ceb5be2b50d54ba290e77d0258ad79f0cc985981) Use scp for file transfers instead of sftp. (@adejanovski)
- [4fa9685](https://github.com/spotify/cstar/commit/4fa96854b6ce103f59258b02bee051dac367e057) Make ssh2-python the default ssh library (@adejanovski)

### 0.7.1 (2018/10/01 13:16 +00:00)
- [#26](https://github.com/spotify/cstar/pull/26) Fix broken tests with new job settings not correctly parsed from json (@adejanovski)
- [ff33495](https://github.com/spotify/cstar/commit/ff33495ad88e3ebff2f6a803faee4b890489fc01) Fix broken tests with new job settings not correctly parsed from json (@adejanovski)
- [#25](https://github.com/spotify/cstar/pull/25) Fix broken "continue" command which can't deal with the absence of ssh_lib (@adejanovski)
- [fd9ed65](https://github.com/spotify/cstar/commit/fd9ed653efb7b5c5bdff098fde63426e03bbc48b) Fix broken "continue" command which can't deal with the absence of ssh_lib. (@adejanovski)

### 0.7.0 (2018/09/27 14:27 +00:00)
- [#24](https://github.com/spotify/cstar/pull/24) Add installation instructions for OS with libssh2 prior to 1.6.0 (@adejanovski)
- [caafcfb](https://github.com/spotify/cstar/commit/caafcfb6f9c5d75a771bd1350598b908868a13fb) Compact the install procedure (@adejanovski)
- [fc677ef](https://github.com/spotify/cstar/commit/fc677efec0ee7f9442c6cf8cf23911c507eea73c) Add installation instructions for OS with libssh2 prior to 1.6.0 (@adejanovski)
- [#23](https://github.com/spotify/cstar/pull/23) Fix for the describecluster issue with locally replicated system ks (@adejanovski)
- [326522a](https://github.com/spotify/cstar/commit/326522ad0c40f354f2aca8f74ffe87d8468533eb) Fix for the describecluster issue with locally replicated system ks (@adejanovski)
- [19eb923](https://github.com/spotify/cstar/commit/19eb9238b6246acbb67a98f9df195b546bbd064d) Fix requirements in setup.py (@Bj0rnen)
- [#16](https://github.com/spotify/cstar/pull/16) Allow to use ssh2-python instead of paramiko for SSH operations (@adejanovski)
- [#22](https://github.com/spotify/cstar/pull/22) Fix cfstats parsing with 3.11 and allow describering to fail with system* keyspaces (@adejanovski)
- [64fc071](https://github.com/spotify/cstar/commit/64fc0711561b28ad5123d4ef4609a86a864b5903) Use a resource file to store the remote shell job instead of a string variable (@adejanovski)
- [348492e](https://github.com/spotify/cstar/commit/348492e43e2646b61c47dae940b152dfeb0c3003) Fix cfstats parsing with 3.11 and allow describering to fail with system* keyspaces (@adejanovski)
- [343e22a](https://github.com/spotify/cstar/commit/343e22aba2da16e0192a1fa4e7a155d6199f141a) Code fixes following PR review. (@adejanovski)
- [#18](https://github.com/spotify/cstar/pull/18) Reduce verbosity of DNS preheating for IPs without a reverse DNS entry (@rborer)
- [bcf725e](https://github.com/spotify/cstar/commit/bcf725ea19be6fd7937788951d817ed924d1cc75) Use lambda expression for nicer syntax (@rborer)
- [7810efc](https://github.com/spotify/cstar/commit/7810efc0cb12d66eeeae17e312769d1b0acf1737) Boost performance by processing results in bulks rather than one by one
- [9f81a27](https://github.com/spotify/cstar/commit/9f81a2766d3a52f585f02b937ed4cb5f97186aaa) Reduce verbosity of DNS preheating for IPs without a reverse DNS entry (@rborer)

### 0.6.0 (2018/09/06 15:42 +00:00)
- [#17](https://github.com/spotify/cstar/pull/17) Only consider node 'up' if state is 'Normal' (@spotify)
- [25c7d75](https://github.com/spotify/cstar/commit/25c7d75c621d527aac80f748c6999b117c4ef296) Add test case (@Bj0rnen)
- [241ff83](https://github.com/spotify/cstar/commit/241ff83a85a57d9ca6820fe657b928ca759f7425) Only consider node 'up' if state is 'Normal' (@Bj0rnen)
- [258841d](https://github.com/spotify/cstar/commit/258841db62a174c580e5b5b40357fd14ebfc956b) Allow to use ssh2-python instead of paramiko for SSH operations (@adejanovski)

### 0.5.1 (2018/09/04 14:26 +00:00)
- [#15](https://github.com/spotify/cstar/pull/15) fix cstarpar to be compatible with the new auth capabilities (@adejanovski)
- [75c225c](https://github.com/spotify/cstar/commit/75c225ccc9253286dc5daf64fbdbbda5ccef2720) fix cstarpar to be compatible with the new auth capabilities

### 0.5.0 (2018/09/03 12:44 +00:00)
- [64e1021](https://github.com/spotify/cstar/commit/64e1021b478de4b4335cba3ed65e6af2bea9c9c7) Bump version to less intimidating 0.5.0 (@Bj0rnen)
- [#12](https://github.com/spotify/cstar/pull/12) Allows to continue a cstar job by replaying the command on failed nodes (@adejanovski)
- [bc50eb0](https://github.com/spotify/cstar/commit/bc50eb033f507f3861f694aca541446cc1f6759c) Allows to continue a cstar job by replaying the command on failed nodes
- [#11](https://github.com/spotify/cstar/pull/11) Video of usage in README (@spotify)
- [11a192d](https://github.com/spotify/cstar/commit/11a192da72194229f4fe5b27165b938812afbe52) video of usage in README (@emmmile)
- [#10](https://github.com/spotify/cstar/pull/10) Remove print command (@spotify)
- [3204534](https://github.com/spotify/cstar/commit/3204534c0fc3ff042b82eade44554aac0a181668) remove print command (@emmmile)
- [#9](https://github.com/spotify/cstar/pull/9) Added a couple of badges to README (@spotify)
- [afa6003](https://github.com/spotify/cstar/commit/afa600334088f3beacf9b4f9f2ab2b35aa8fb42d) added a couple of badges to README (@emmmile)
- [#8](https://github.com/spotify/cstar/pull/8) Fix security problem in dependency (@spotify)
- [#5](https://github.com/spotify/cstar/pull/5) Clarify description of --dc-parallelism (@spotify)
- [5fc1069](https://github.com/spotify/cstar/commit/5fc10695f1227e81e1565cd67bd7825f0753b594) Merge branch 'master' into protocol7-typo-1 (@liljencrantz)
- [da0e0fe](https://github.com/spotify/cstar/commit/da0e0fe843a035f2d5bc1d31d0b5b563e622aec9) Fix security problem in dependency (@liljencrantz)
- [#7](https://github.com/spotify/cstar/pull/7) Typo on string #21 & #127 (@kant)
- [#6](https://github.com/spotify/cstar/pull/6) Support for ssh username, password and identity file (@thelastpickle)
- [9b9b900](https://github.com/spotify/cstar/commit/9b9b9006fabcf5871e384111dabe53740e918783) Typo on string #21 & #127 (@kant)
- [8a5caa2](https://github.com/spotify/cstar/commit/8a5caa29689eb6411f4a14e48f5bf30217ab39d8) Support for ssh username, password and identity file (@adejanovski)
- [199e79d](https://github.com/spotify/cstar/commit/199e79df17a2476d56b595fd6064bb4082df224e) Clarify description of --dc-parallelism (@protocol7)
