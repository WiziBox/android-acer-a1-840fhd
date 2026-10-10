/* SPDX-License-Identifier: Apache-2.0
 * i386 C variadic tail-call: preserve all proprietary perform arguments and
 * replace only the first module pointer. No guessed argument count or ABI.
 */
#if !defined(__i386__)
#error "This thunk is only valid for the measured 32-bit Acer x86 ABI"
#endif
    .text
    .p2align 4
    .globl acer_gralloc_perform
    .type acer_gralloc_perform,@function
    .hidden acer_gralloc_original_module
    .hidden acer_gralloc_original_perform
acer_gralloc_perform:
    call .Lgetpc
.Lgetpc:
    popl %eax
    addl $_GLOBAL_OFFSET_TABLE_+(. - .Lgetpc), %eax
    movl acer_gralloc_original_perform@GOTOFF(%eax), %edx
    testl %edx, %edx
    jz .Lunsupported
    movl acer_gralloc_original_module@GOTOFF(%eax), %eax
    movl %eax, 4(%esp)
    jmp *%edx
.Lunsupported:
    movl $-38, %eax /* -ENOSYS, not a fake successful perform */
    ret
    .size acer_gralloc_perform, .-acer_gralloc_perform
    .section .note.GNU-stack,"",@progbits
