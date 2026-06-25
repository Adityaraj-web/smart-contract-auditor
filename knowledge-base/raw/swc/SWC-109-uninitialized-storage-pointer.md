---
category: uninitialized-storage-pointer
swc_id: SWC-109
source_type: swc
title: Uninitialized Storage Pointer
source_url: https://swcregistry.io/docs/SWC-109
---

Solidity variables of complex types (structs, arrays, mappings)
declared inside a function default to either `storage` or `memory`
depending on context and compiler version, and in older Solidity
versions this default wasn't always obvious or safe. A local variable
that's implicitly typed as `storage` but never explicitly assigned to a
specific existing storage variable doesn't point to "nothing" — storage
pointers default to slot 0 — so it silently points at whatever state
variable happens to occupy that contract's first storage slot,
frequently something critical like the owner address or a core balance
mapping.

Any write to that uninitialized pointer is then actually a write to
slot 0's real variable, not to a harmless throwaway value as the
developer likely intended — effectively giving an attacker, or even
ordinary contract logic, an unintended way to overwrite sensitive state
without any access-control check standing in the way, since the write
doesn't go through whatever function is supposed to guard that
variable.

Modern Solidity compilers (0.5.0 and later) catch most of these cases
at compile time and refuse to compile ambiguous storage references, but
the pattern remains relevant when analyzing or learning from older
contracts, and is still worth a static analyzer flagging explicitly
rather than relying solely on compiler version.