// src/components/CarDoor.jsx
import React, { useRef, useEffect, useState } from 'react';
import { useGLTF, useAnimations } from '@react-three/drei';
import * as THREE from 'three';

export default function CarDoor() {
  const group = useRef();
  const { scene, animations } = useGLTF('/models/car.glb'); // replace with your path
  const { mixer } = useAnimations(animations, group);
  const [doorOpen, setDoorOpen] = useState(false);
  const actionRef = useRef(null);
  const clip = animations[0]; // assumes door open is the only animation

  useEffect(() => {
    const action = mixer.clipAction(clip);
    action.setLoop(THREE.LoopOnce);
    action.clampWhenFinished = true;
    actionRef.current = action;
  }, [clip, mixer]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'd' || e.key === 'D') {
        const action = actionRef.current;
        if (!action) return;

        action.reset();
        if (!doorOpen) {
          action.timeScale = 1;
          action.time = 0;
        } else {
          action.timeScale = -1;
          action.time = clip.duration;
        }

        action.play();
        setDoorOpen(!doorOpen);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [doorOpen, clip]);

  return <primitive ref={group} object={scene} />;
}
