from moviepy import *
import numpy as np

class TransitionEffect:
    @staticmethod
    def get_available_transitions():
        """Retorna una lista de las transiciones disponibles."""
        return ['none', 'dissolve']
    
    @staticmethod
    def apply_transition(clips, transition_type='none', transition_duration=1.0):
        """Aplica una transición específica a una lista de clips.
        
        Args:
            clips: Lista de clips de video
            transition_type: Tipo de transición ('none', 'dissolve')
            transition_duration: Duración de la transición en segundos
            
        Returns:
            Un clip final con las transiciones aplicadas
        """
        if not clips:
            return None
            
        if len(clips) == 1 or transition_duration <= 0 or transition_type == 'none':
            return clips[0] if len(clips) == 1 else concatenate_videoclips(clips)
        
        if transition_type == 'dissolve':
            return TransitionEffect._apply_dissolve_transitions(clips, transition_duration)
        
        # Si el tipo de transición no es reconocido, usar concatenación simple
        return concatenate_videoclips(clips)
    
    @staticmethod
    def _dissolve_transition(clip1, clip2, duration):
        """Crea una transición de disolución entre dos clips."""
        if clip1.duration <= duration or clip2.duration <= duration:
            duration = min(duration, clip1.duration / 2, clip2.duration / 2)
            print(f"Advertencia: Duración de transición ajustada a {duration} segundos")
        
        start_time = clip1.duration - duration
        
        def blend(frame1, frame2, progress):
            return (1 - progress) * frame1 + progress * frame2
        
        def make_frame(t):
            if t < start_time:
                return clip1.get_frame(t)
            elif t >= clip1.duration:
                return clip2.get_frame(t - start_time)
            else:
                progress = (t - start_time) / duration
                frame1 = clip1.get_frame(t)
                frame2 = clip2.get_frame(t - start_time)
                return blend(frame1, frame2, progress)
        
        final_duration = clip1.duration + clip2.duration - duration
        final_clip = VideoClip(make_frame, duration=final_duration)
        final_clip = final_clip.with_fps(24)
        
        # Manejar el audio
        if hasattr(clip1, 'audio') and clip1.audio is not None and hasattr(clip2, 'audio') and clip2.audio is not None:
            audio1 = clip1.audio
            audio2 = clip2.audio.with_start(start_time)
            final_clip = final_clip.with_audio(CompositeAudioClip([audio1, audio2]))
        elif hasattr(clip1, 'audio') and clip1.audio is not None:
            final_clip = final_clip.with_audio(clip1.audio)
        elif hasattr(clip2, 'audio') and clip2.audio is not None:
            audio2 = clip2.audio.with_start(start_time)
            final_clip = final_clip.with_audio(audio2)
        
        return final_clip
    
    @staticmethod
    def _apply_dissolve_transitions(clips, transition_duration=1.0):
        """Aplica transiciones de disolución entre una lista de clips."""
        if not clips:
            return None
            
        if len(clips) == 1 or transition_duration <= 0:
            return clips[0] if len(clips) == 1 else concatenate_videoclips(clips)
        
        final_clip = clips[0]
        for i in range(1, len(clips)):
            final_clip = TransitionEffect._dissolve_transition(final_clip, clips[i], transition_duration)
        
        return final_clip