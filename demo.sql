-- demo.sql

PRAGMA foreign_keys=ON;

INSERT INTO users (username, password_hash) VALUES
('DemoKäyttäjä', 'scrypt:32768:8:1$kjjPB1yKVg6qR8Ql$d15e967943ce1872c5cafb9cee3bb2de7a66c0d34f262136191d663bfea9833590b7f94d3d1152d1f54045b1b790f60cf4d660c0ef71c199a0c986a0a711fe5d');

INSERT INTO devices (name, description, created_by) VALUES
('PineView.A1_Demo',
    'Platform: Atom "Pine Trail"
Stepping: A1 (Demo Board)
IFWI: PV_ATOM_0.9.123
Memory: 2GB DDR2 Onboard
Use: Low-power demo applications',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä')),

('IronLake.B0_Test',
    'Platform: "Arrandale/Clarkdale" (Westmere gen)
Stepping: B0 (Test System)
Graphics: Intel HD Graphics (1st Gen)
Memory: 4GB DDR3 1066MHz
Notes: Early integrated graphics test unit.',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä')),

('SandyBridge.ES_Server',
    'Platform: Sandy Bridge-EP (Server)
Stepping: C1 (Engineering Sample)
BIOS Version: SB_EP_008.PRE
CPU Sockets: 2
Memory: 32GB DDR3 ECC
Purpose: Server validation platform.',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä')),

('IvyBridge.Mobile_UX',
    'Platform: Ivy Bridge ULV (Mobile)
Stepping: E1
Touchscreen: Yes (Demo Unit)
Storage: 128GB mSATA SSD
OS: Demo Linux Distro',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä')),

('Haswell.DT_Proto',
    'Platform: Haswell Desktop (LGA1150)
Stepping: C0 (Prototype)
Power Supply: External Lab PSU
Cooling: Custom Heatsink
Notes: For FIVR testing and early performance numbers.',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä')),

('BayTrail.Tablet_Ref',
    'Platform: Atom "Bay Trail-T"
Stepping: B3 (Reference Design)
Display: 10-inch Tablet Panel
Battery: Internal Li-Po (Test Cell)
Connectivity: Wi-Fi/BT (Early Module)',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä')),

('Nehalem.EarlyBird',
    'Platform: Nehalem (Core i7 1st Gen)
Stepping: B0
Memory: 6GB Triple-Channel DDR3
Chipset: X58
Notes: One of the first off the line.',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä')),

('Lynnfield.P55_Demo',
    'Platform: Lynnfield (Core i5/i7)
Stepping: B1
Motherboard: P55 Chipset Demo Board
Graphics: Discrete GPU required
Use: Mainstream desktop performance showcase.',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä')),

('Clarkdale.H55_Media',
    'Platform: Clarkdale (Core i3/i5 with IGP)
Stepping: C2
Output: HDMI 1.3
Use: HTPC and media playback demonstrations.',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä')),

('Wolfdale.Core2_Classic',
    'Platform: Core 2 Duo "Wolfdale"
Stepping: E0
FSB: 1333MHz
Memory: 4GB DDR2 800MHz
Era: Pre-Core i architecture.',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä')),

('Conroe.FirstCore2',
    'Platform: Core 2 Duo "Conroe"
Stepping: B2
Socket: LGA775
Notes: The original Core microarchitecture.',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä')),

('Penryn.MobileWorkstation',
    'Platform: Core 2 Duo Mobile "Penryn"
Stepping: C0/M0
Screen: 15.4" High-Res (Demo)
Use: Mobile workstation prototype.',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä')),

('Prescott.NetburstArch',
    'Platform: Pentium 4 "Prescott"
Stepping: C0
Architecture: NetBurst
Clock Speed: 3.2 GHz (High Heat Output Demo)
Notes: Known for its thermal challenges.',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä')),

('Northwood.P4_Stable',
    'Platform: Pentium 4 "Northwood"
Stepping: D1
FSB: 800MHz
HyperThreading: Yes
Notes: A very popular P4 iteration.',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä')),

('Willamette.OriginalP4',
    'Platform: Pentium 4 "Willamette"
Stepping: B2
Memory: RDRAM (Rambus)
Notes: The very first Pentium 4.',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä')),

('Tualatin.LateP3',
    'Platform: Pentium III "Tualatin"
Stepping: tA1
Cache: 512KB L2
Process: 0.13 micron
Notes: Final and most refined P3.',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä')),

('Coppermine.P3_Common',
    'Platform: Pentium III "Coppermine"
Stepping: cC0
Slot/Socket: Slot 1 or Socket 370
Notes: Widely adopted P3 core.',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä')),

('Katmai.FirstP3',
    'Platform: Pentium III "Katmai"
Stepping: kB0
SSE: Introduced
Notes: First CPU with SSE instructions.',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä')),

('Deschutes.P2_Slot1',
    'Platform: Pentium II "Deschutes"
Stepping: dB0
Form Factor: Slot 1 SECC2
Notes: Refined Pentium II.',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä')),

('Klamath.OriginalP2',
    'Platform: Pentium II "Klamath"
Stepping: kA0
L2 Cache: External, 512KB, half-speed
Notes: Introduced MMX technology prominently.',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä')),

('PentiumMMX.P55C',
    'Platform: Pentium MMX "P55C"
Stepping: xB1
MMX: Yes
Socket: Socket 7
Notes: Enhanced Pentium with MMX.',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä')),

('PentiumClassic.P54C',
    'Platform: Pentium Classic "P54C"
Stepping: sSpec Q065 (example)
Clock: 75-200MHz
Notes: The original superscalar Pentium.',
    (SELECT id FROM users WHERE username = 'DemoKäyttäjä'));

INSERT INTO comments (device_id, user_id, content) VALUES
((SELECT id FROM devices WHERE name = 'PineView.A1_Demo'), (SELECT id FROM users WHERE username = 'DemoKäyttäjä'), 'This PineView sample is quite basic.
Good for low-power scenarios.'),
((SELECT id FROM devices WHERE name = 'IronLake.B0_Test'), (SELECT id FROM users WHERE username = 'DemoKäyttäjä'), 'Testing integrated graphics performance.
Seems okay for its age.'),
((SELECT id FROM devices WHERE name = 'Haswell.DT_Proto'), (SELECT id FROM users WHERE username = 'DemoKäyttäjä'), 'FIVR seems to be working as expected on this Haswell prototype.');

INSERT INTO reservations (user_id, device_id, reserved_until) VALUES
((SELECT id FROM users WHERE username = 'DemoKäyttäjä'), (SELECT id FROM devices WHERE name = 'SandyBridge.ES_Server'), strftime('%s','now', '+2 days')),
((SELECT id FROM users WHERE username = 'DemoKäyttäjä'), (SELECT id FROM devices WHERE name = 'Haswell.DT_Proto'), strftime('%s','now', '+5 days'));

SELECT 'Demo data inserted successfully.' AS status;