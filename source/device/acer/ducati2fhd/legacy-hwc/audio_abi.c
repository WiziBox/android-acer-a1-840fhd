/* SPDX-License-Identifier: Apache-2.0
 * WiziBox Android 9 port implementation; modified 2026-10-11.
 */
/* Intel stock x86 ABI verified from legacy_adev_open/out/input assembly.
 * Real callbacks retain original objects; unsupported appended methods NULL.
 * Device: private pointer at 0x88. Output: flush0x48/timestamp0x5c/private0x64.
 */
#include <hardware/audio.h>
#include <stddef.h>
#include <stdlib.h>
#include <errno.h>
struct device_proxy { audio_hw_device_t api; audio_hw_device_t *raw; };
struct stream_proxy { union { audio_stream_out_t out; audio_stream_in_t in; } api; void *raw; };
_Static_assert(sizeof(void *) == 4, "Intel x86 only");
_Static_assert(sizeof(audio_stream_t) == 0x38, "common stream ABI");
_Static_assert(offsetof(audio_hw_device_t, get_microphones) == 0x7c, "device ABI");
#define D(d) (((const struct device_proxy *)(d))->raw)
#define S(s) (((const struct stream_proxy *)(s))->raw)
#define FN(type, field, raw, off) (*(__typeof__(((type *)0)->field) *)((char *)(raw)+(off)))
#define DF(field, raw) FN(audio_hw_device_t, field, raw, offsetof(audio_hw_device_t, field))
#define SF(field, raw) FN(audio_stream_t, field, raw, offsetof(audio_stream_t, field))
#define OF(field, raw, off) FN(audio_stream_out_t, field, raw, off)
#define IF(field, raw) FN(audio_stream_in_t, field, raw, offsetof(audio_stream_in_t, field))
#define DEV(ret, field, sig, args) static ret d_##field sig { return DF(field,D(d)) args; }
DEV(int, init_check, (const audio_hw_device_t *d), (D(d)))
DEV(int, set_voice_volume, (audio_hw_device_t *d,float v), (D(d),v))
DEV(int, set_master_volume, (audio_hw_device_t *d,float v), (D(d),v))
DEV(int, get_master_volume, (audio_hw_device_t *d,float *v), (D(d),v))
DEV(int, set_mode, (audio_hw_device_t *d,audio_mode_t m), (D(d),m))
DEV(int, set_mic_mute, (audio_hw_device_t *d,bool v), (D(d),v))
DEV(int, get_mic_mute, (const audio_hw_device_t *d,bool *v), (D(d),v))
DEV(int, set_parameters, (audio_hw_device_t *d,const char *v), (D(d),v))
DEV(char *, get_parameters, (const audio_hw_device_t *d,const char *v), (D(d),v))
DEV(size_t, get_input_buffer_size, (const audio_hw_device_t *d,const struct audio_config *c), (D(d),c))
static int d_dump(const audio_hw_device_t *d,int fd) { return FN(audio_hw_device_t,dump,D(d),0x7c)(D(d),fd); }
static int d_close(hw_device_t *d) { int rc=D(d)->common.close(&D(d)->common); free(d); return rc; }
#define COMMON(ret, field, sig, args) static ret s_##field sig { return SF(field,S(s)) args; }
COMMON(uint32_t,get_sample_rate,(const audio_stream_t *s),(S(s)))
COMMON(int,set_sample_rate,(audio_stream_t *s,uint32_t r),(S(s),r))
COMMON(size_t,get_buffer_size,(const audio_stream_t *s),(S(s)))
COMMON(audio_channel_mask_t,get_channels,(const audio_stream_t *s),(S(s)))
COMMON(audio_format_t,get_format,(const audio_stream_t *s),(S(s)))
COMMON(int,set_format,(audio_stream_t *s,audio_format_t f),(S(s),f))
COMMON(int,standby,(audio_stream_t *s),(S(s)))
COMMON(int,dump,(const audio_stream_t *s,int fd),(S(s),fd))
COMMON(int,set_parameters,(audio_stream_t *s,const char *v),(S(s),v))
COMMON(char *,get_parameters,(const audio_stream_t *s,const char *v),(S(s),v))
COMMON(int,add_audio_effect,(const audio_stream_t *s,effect_handle_t e),(S(s),e))
COMMON(int,remove_audio_effect,(const audio_stream_t *s,effect_handle_t e),(S(s),e))
#define OUT(ret, field, off, sig, args) static ret o_##field sig { return OF(field,S(s),off) args; }
OUT(uint32_t,get_latency,0x38,(const audio_stream_out_t *s),(S(s)))
OUT(int,set_volume,0x3c,(audio_stream_out_t *s,float l,float r),(S(s),l,r))
OUT(ssize_t,write,0x40,(audio_stream_out_t *s,const void *b,size_t n),(S(s),b,n))
OUT(int,get_render_position,0x44,(const audio_stream_out_t *s,uint32_t *v),(S(s),v))
OUT(int,flush,0x48,(audio_stream_out_t *s),(S(s)))
OUT(int,get_next_write_timestamp,0x5c,(const audio_stream_out_t *s,int64_t *v),(S(s),v))
#define IN(ret,field,sig,args) static ret i_##field sig { return IF(field,S(s)) args; }
IN(int,set_gain,(audio_stream_in_t *s,float v),(S(s),v))
IN(ssize_t,read,(audio_stream_in_t *s,void *b,size_t n),(S(s),b,n))
IN(uint32_t,get_input_frames_lost,(audio_stream_in_t *s),(S(s)))
static void wrap_common(audio_stream_t *api, void *raw) {
#define SET(field) if(SF(field,raw)) api->field=s_##field
    SET(get_sample_rate); SET(set_sample_rate); SET(get_buffer_size);
    SET(get_channels); SET(get_format); SET(set_format); SET(standby); SET(dump);
    SET(set_parameters); SET(get_parameters); SET(add_audio_effect); SET(remove_audio_effect);
#undef SET
    /* Deprecated routing callbacks are NULL in this exact stock HAL. */
}
static int d_open_output_stream(audio_hw_device_t *d,audio_io_handle_t h,audio_devices_t devices,audio_output_flags_t flags,struct audio_config *c,audio_stream_out_t **out,const char *address) {
    audio_stream_out_t *raw=NULL;
    int rc=DF(open_output_stream,D(d))(D(d),h,devices,flags,c,&raw,address);
    if(rc) return rc;
    struct stream_proxy *p=calloc(1,sizeof(*p));
    if(!p) { DF(close_output_stream,D(d))(D(d),raw); return -ENOMEM; }
    p->raw=raw; wrap_common(&p->api.out.common,raw);
#define SET(field,off) if(OF(field,raw,off)) p->api.out.field=o_##field
    SET(get_latency,0x38); SET(set_volume,0x3c); SET(write,0x40);
    SET(get_render_position,0x44); SET(flush,0x48); SET(get_next_write_timestamp,0x5c);
#undef SET
    *out=&p->api.out; return 0;
}
static void d_close_output_stream(audio_hw_device_t *d,audio_stream_out_t *s) { DF(close_output_stream,D(d))(D(d),S(s)); free(s); }
static int d_open_input_stream(audio_hw_device_t *d,audio_io_handle_t h,audio_devices_t devices,struct audio_config *c,audio_stream_in_t **in,audio_input_flags_t flags,const char *address,audio_source_t source) {
    audio_stream_in_t *raw=NULL;
    int rc=DF(open_input_stream,D(d))(D(d),h,devices,c,&raw,flags,address,source);
    if(rc) return rc;
    struct stream_proxy *p=calloc(1,sizeof(*p));
    if(!p) { DF(close_input_stream,D(d))(D(d),raw); return -ENOMEM; }
    p->raw=raw; wrap_common(&p->api.in.common,raw);
#define SET(field) if(IF(field,raw)) p->api.in.field=i_##field
    SET(set_gain); SET(read); SET(get_input_frames_lost);
#undef SET
    *in=&p->api.in; return 0;
}
static void d_close_input_stream(audio_hw_device_t *d,audio_stream_in_t *s) { DF(close_input_stream,D(d))(D(d),S(s)); free(s); }
int acer_audio_wrap(hw_device_t **device);
int acer_audio_wrap(hw_device_t **device) {
    struct device_proxy *p=calloc(1,sizeof(*p));
    if(!p) { (*device)->close(*device); *device=NULL; return -ENOMEM; }
    p->raw=(audio_hw_device_t *)*device; p->api.common=p->raw->common;
    p->api.common.close=d_close;
#define SET(field) if(DF(field,p->raw)) p->api.field=d_##field
    SET(init_check); SET(set_voice_volume); SET(set_master_volume); SET(get_master_volume);
    SET(set_mode); SET(set_mic_mute); SET(get_mic_mute); SET(set_parameters); SET(get_parameters);
    SET(get_input_buffer_size); SET(open_output_stream); SET(close_output_stream);
    SET(open_input_stream); SET(close_input_stream);
#undef SET
    p->api.dump=d_dump;
    /* Stock calloc leaves 0x80/0x84 master mute hooks NULL, API2 has no patches.
     * Never read 0x88 as a callback: it is AudioHardwareALSA's object pointer. */
    *device=&p->api.common; return 0;
}
