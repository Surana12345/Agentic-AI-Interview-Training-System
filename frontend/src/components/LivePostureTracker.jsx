import React, { useRef, useEffect, useState } from "react";
import * as tf from "@tensorflow/tfjs";
import * as cocoSsd from "@tensorflow-models/coco-ssd";

const LivePostureTracker = ({ onStatsUpdate, isRecording, onVideoReady, onMultiplePeopleWarning, onMultiplePeopleEnd }) => {
    const videoRef = useRef(null);
    const [feedback, setFeedback] = useState("Waiting to start...");
    const [cameraError, setCameraError] = useState(null);
    const [cameraActive, setCameraActive] = useState(false);

    const isRecordingRef = useRef(isRecording);
    const onStatsUpdateRef = useRef(onStatsUpdate);

    // Persistent refs for camera/ML cleanup
    const cameraRef = useRef(null);
    const poseRef = useRef(null);
    const faceMeshRef = useRef(null);
    const objectModelRef = useRef(null); // COCO-SSD
    const streamRef = useRef(null);

    // Multi-Person warning states
    const warningsRef = useRef(0);
    const lastWarningTime = useRef(Date.now());

    // === COMPREHENSIVE FRAME-RATIO + BEHAVIORAL SCORING ===
    const frameCountersRef = useRef({
        totalFrames: 0,
        presentFrames: 0,
        goodPostureFrames: 0,
        goodEyeContactFrames: 0,
        absentCount: 0,
        lookedAway: 0,
        slouched: 0,
        unevenShoulders: 0,
        phoneDetected: 0,
        // Advanced behavioral metrics
        headMovementCount: 0,    // Sudden head direction changes
        postureShiftCount: 0,    // Times posture toggled good↔bad
        fidgetCount: 0,          // Rapid hand/wrist movement spikes
        engagedFrames: 0,        // Frames with full engagement (good posture + eye contact + still)
    });

    // SEPARATE debounce timers
    const lastPenaltyTimeRef = useRef({
        absent: 0, lookedAway: 0, slouched: 0, unevenShoulders: 0, phone: 0
    });

    // Previous-frame state for detecting transitions/movements
    const prevFrameRef = useRef({
        noseX: 0, noseY: 0, wasPostureGood: true, wasEyeGood: true,
        leftWristX: 0, leftWristY: 0, rightWristX: 0, rightWristY: 0,
    });

    // Removed MediaRecorder references

    // Helper: push a COPY of current stats to parent (forces React re-render)
    const pushStats = () => {
        if (onStatsUpdateRef.current) {
            const c = frameCountersRef.current;
            onStatsUpdateRef.current({
                totalFrames: c.totalFrames,
                presentFrames: c.presentFrames,
                goodPostureFrames: c.goodPostureFrames,
                goodEyeContactFrames: c.goodEyeContactFrames,
                absentCount: c.absentCount,
                lookedAway: c.lookedAway,
                slouched: c.slouched,
                unevenShoulders: c.unevenShoulders,
                phoneDetected: c.phoneDetected,
                headMovementCount: c.headMovementCount,
                postureShiftCount: c.postureShiftCount,
                fidgetCount: c.fidgetCount,
                engagedFrames: c.engagedFrames,
            });
        }
    };

    // ── Stop camera and release all media tracks ──
    const stopCamera = () => {
        if (cameraRef.current) {
            cameraRef.current.stop();
            cameraRef.current = null;
        }
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
        if (videoRef.current) {
            videoRef.current.srcObject = null;
        }
        setCameraActive(false);
    };

    useEffect(() => {
        isRecordingRef.current = isRecording;
        onStatsUpdateRef.current = onStatsUpdate;

        if (isRecording) {
            window.isSessionActive = true;
            // Reset ALL counters for new session
            frameCountersRef.current = {
                totalFrames: 0, presentFrames: 0,
                goodPostureFrames: 0, goodEyeContactFrames: 0,
                absentCount: 0, lookedAway: 0, slouched: 0,
                unevenShoulders: 0, phoneDetected: 0,
                headMovementCount: 0, postureShiftCount: 0,
                fidgetCount: 0, engagedFrames: 0,
            };
            lastPenaltyTimeRef.current = {
                absent: 0, lookedAway: 0, slouched: 0, unevenShoulders: 0, phone: 0
            };
            prevFrameRef.current = {
                noseX: 0, noseY: 0, wasPostureGood: true, wasEyeGood: true,
                leftWristX: 0, leftWristY: 0, rightWristX: 0, rightWristY: 0,
            };
            warningsRef.current = 0;
            setFeedback("Initializing...");
            pushStats();
            // Start camera if not already running
            if (!cameraActive) startCameraSystem();
        } else {
            window.isSessionActive = false;
            // Stop camera when session ends
            stopCamera();
        }

        return () => {
            window.isSessionActive = false;
        };
    }, [isRecording]);

    // ── Start camera + ML pipeline ──
    const startCameraSystem = () => {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            setCameraError(
                window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
                    ? "Camera access denied. Please allow camera permissions."
                    : "Camera requires a secure connection. Please use http://localhost:3001 instead."
            );
            setFeedback("Camera unavailable");
            return;
        }

        // Initialize COCO-SSD (Background)
        if (!objectModelRef.current) {
            cocoSsd.load().then(model => {
                objectModelRef.current = model;
            }).catch(e => console.error("COCO-SSD error:", e));
        }

        const pose = new window.Pose({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`,
        });
        poseRef.current = pose;

        pose.setOptions({
            modelComplexity: 1,
            smoothLandmarks: true,
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5,
        });

        pose.onResults((results) => {
            if (!isRecordingRef.current) return;

            const c = frameCountersRef.current;
            const now = Date.now();
            c.totalFrames += 1;

            if (!results.poseLandmarks || results.poseLandmarks.length === 0) {
                setFeedback("⚠️ Subject absent from camera!");
                c.absentCount += 1;
                if (now - lastPenaltyTimeRef.current.absent > 1000) {
                    c.lookedAway += 1;
                    c.slouched += 1;
                    lastPenaltyTimeRef.current.absent = now;
                }
                pushStats();
                return;
            }

            c.presentFrames += 1;
            const landmarks = results.poseLandmarks;
            const nose = landmarks[0];
            const leftEar = landmarks[7];
            const rightEar = landmarks[8];
            const leftShoulder = landmarks[11];
            const rightShoulder = landmarks[12];

            const faceWidth = Math.abs(leftEar.x - rightEar.x);
            if (faceWidth < 0.01) { pushStats(); return; }

            const shoulderDiff = Math.abs(leftShoulder.y - rightShoulder.y);
            const shoulderAvgY = (leftShoulder.y + rightShoulder.y) / 2;
            const shoulderCenterX = (leftShoulder.x + rightShoulder.x) / 2;
            const earAvgY = (leftEar.y + rightEar.y) / 2;

            const pitchDiff = nose.y - earAvgY;
            const isLookingUp = pitchDiff < -(faceWidth * 0.12);
            const isLookingDown = pitchDiff > (faceWidth * 0.35);

            const leftEye = landmarks[2];
            const rightEye = landmarks[5];
            const zDiff = Math.abs(leftEye.z - rightEye.z);
            const isLookingAway = zDiff > 0.06 || isLookingUp || isLookingDown;

            const earCenterX = (leftEar.x + rightEar.x) / 2;
            const headTilt = Math.abs(nose.x - earCenterX);
            const isHeadTilted = headTilt > faceWidth * 0.35;

            const neckLength = Math.abs(shoulderAvgY - nose.y);
            const neckToFaceRatio = neckLength / faceWidth;
            const isSlouching = neckToFaceRatio < 1.2;

            const shoulderUnevenRatio = shoulderDiff / faceWidth;
            const isUnevenShoulders = shoulderUnevenRatio > 0.25;

            const leanOffset = Math.abs(nose.x - shoulderCenterX);
            const isLeaning = leanOffset > faceWidth * 0.5;

            let framePostureGood = true;
            let frameEyeContactGood = true;
            let currentWarning = null;

            if (isLookingAway) {
                currentWarning = currentWarning || "Maintain eye contact with camera";
                frameEyeContactGood = false;
                if (now - lastPenaltyTimeRef.current.lookedAway > 1000) { c.lookedAway += 1; lastPenaltyTimeRef.current.lookedAway = now; }
            }
            if (isSlouching) {
                currentWarning = currentWarning || "Slouching detected — sit up straight";
                framePostureGood = false;
                if (now - lastPenaltyTimeRef.current.slouched > 1000) { c.slouched += 1; lastPenaltyTimeRef.current.slouched = now; }
            }
            if (isUnevenShoulders) {
                currentWarning = currentWarning || "Shoulders uneven — sit balanced";
                framePostureGood = false;
                if (now - lastPenaltyTimeRef.current.unevenShoulders > 1000) { c.unevenShoulders += 1; lastPenaltyTimeRef.current.unevenShoulders = now; }
            }
            if (isLeaning) { currentWarning = currentWarning || "Leaning to one side"; framePostureGood = false; }
            if (isHeadTilted) { currentWarning = currentWarning || "Head tilted — keep head level"; framePostureGood = false; }

            if (framePostureGood) c.goodPostureFrames += 1;
            if (frameEyeContactGood) c.goodEyeContactFrames += 1;

            const prev = prevFrameRef.current;
            if (prev.noseX > 0) {
                const headDelta = Math.hypot(nose.x - prev.noseX, nose.y - prev.noseY);
                if (headDelta > 0.04) c.headMovementCount += 1;
            }
            prev.noseX = nose.x; prev.noseY = nose.y;
            if (prev.wasPostureGood !== framePostureGood) c.postureShiftCount += 1;
            prev.wasPostureGood = framePostureGood;
            prev.wasEyeGood = frameEyeContactGood;

            const shoulderMidX = shoulderCenterX;
            const shoulderMidY = shoulderAvgY;
            if (prev.leftWristX > 0) {
                const shoulderDelta = Math.hypot(shoulderMidX - prev.leftWristX, shoulderMidY - prev.leftWristY);
                if (shoulderDelta > 0.03) c.fidgetCount += 1;
            }
            prev.leftWristX = shoulderMidX; prev.leftWristY = shoulderMidY;

            if (framePostureGood && frameEyeContactGood) c.engagedFrames += 1;
            setFeedback(currentWarning || "Good posture");
            pushStats();
        });

        const faceMesh = new window.FaceMesh({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`,
        });
        faceMeshRef.current = faceMesh;

        faceMesh.setOptions({
            maxNumFaces: 2,
            refineLandmarks: true,
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5
        });

        faceMesh.onResults((results) => {
            if (!isRecordingRef.current) return;
            if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 1) {
                const now = Date.now();
                if (now - lastWarningTime.current > 4000) {
                    warningsRef.current += 1;
                    lastWarningTime.current = now;
                    setFeedback("Multiple people detected!");
                    if (warningsRef.current <= 3) { if (onMultiplePeopleWarning) onMultiplePeopleWarning(warningsRef.current); }
                    else { if (onMultiplePeopleEnd) onMultiplePeopleEnd(); }
                }
                return;
            }
        });

        if (videoRef.current) {
            let isProcessingFrame = false;
            let lastFrameTime = 0;
            let lastFaceTime = 0;
            let lastObjectTime = 0;

            const camera = new window.Camera(videoRef.current, {
                onFrame: async () => {
                    const now = Date.now();
                    if (isProcessingFrame || now - lastFrameTime < 250) return;
                    isProcessingFrame = true;
                    lastFrameTime = now;
                    try {
                        if (poseRef.current) await poseRef.current.send({ image: videoRef.current });
                        if (faceMeshRef.current && now - lastFaceTime > 2000) {
                            lastFaceTime = now;
                            await faceMeshRef.current.send({ image: videoRef.current });
                        }
                        
                        // Object Detection for Cell Phone (~every 500ms)
                        if (objectModelRef.current && now - lastObjectTime > 500 && isRecordingRef.current) {
                            lastObjectTime = now;
                            const predictions = await objectModelRef.current.detect(videoRef.current);
                            // Lower threshold to 0.4 for better mobile detection; include 'remote' as fallback
                            const hasPhone = predictions.some(p => (p.class === "cell phone" || p.class === "remote") && p.score > 0.4);
                            if (hasPhone) {
                                const c = frameCountersRef.current;
                                if (now - lastPenaltyTimeRef.current.phone > 1000) {
                                    c.phoneDetected += 1;
                                    lastPenaltyTimeRef.current.phone = now;
                                    setFeedback("⚠️ Mobile phone detected in frame!");
                                }
                            }
                        }
                    } catch (err) {
                        console.error("Frame processing error:", err);
                    } finally {
                        isProcessingFrame = false;
                    }
                },
                width: 320, height: 240,
            });
            cameraRef.current = camera;

            camera.start().then(() => {
                setCameraActive(true);
                // Store the stream for cleanup
                if (videoRef.current && videoRef.current.srcObject) {
                    streamRef.current = videoRef.current.srcObject;
                }
            }).catch((err) => {
                console.error("Camera start error:", err);
                setCameraError("Could not start camera. Check permissions.");
            });
        }
    };

    // Cleanup on component unmount
    useEffect(() => {
        return () => {
            stopCamera();
            if (poseRef.current) { poseRef.current.close(); poseRef.current = null; }
            if (faceMeshRef.current) { faceMeshRef.current.close(); faceMeshRef.current = null; }
        };
    }, []);

    if (cameraError) {
        return (
            <div style={{
                width: '100%', borderRadius: '12px', overflow: 'hidden',
                backgroundColor: '#0a0a0a', color: '#94a3b8',
                display: 'flex', flexDirection: 'column', alignItems: 'center',
                justifyContent: 'center', minHeight: '320px', padding: '30px',
                textAlign: 'center', border: '1px solid #1f2937',
            }}>
                <div style={{ fontSize: '2rem', marginBottom: '12px', opacity: 0.4 }}>&#x1F4F7;</div>
                <div style={{ fontSize: '0.95rem', fontWeight: '600', color: '#e2e8f0', marginBottom: '8px' }}>
                    Camera Unavailable
                </div>
                <div style={{ fontSize: '0.82rem', lineHeight: '1.5', maxWidth: '300px' }}>
                    {cameraError}
                </div>
            </div>
        );
    }

    return (
        <div style={{ position: 'relative', width: '100%', borderRadius: '12px', overflow: 'hidden' }}>
            <video ref={videoRef} style={{ width: '100%', display: 'block', transform: 'scaleX(-1)' }} />
            <div style={{
                position: 'absolute', bottom: '10px', left: '10px',
                backgroundColor: feedback === "Good posture" ? 'rgba(16,185,129,0.85)' : 'rgba(239,68,68,0.85)',
                color: 'white',
                padding: '6px 14px', borderRadius: '20px', fontSize: '0.82rem',
                fontWeight: '500', transition: 'all 0.3s ease',
                backdropFilter: 'blur(8px)',
            }}>
                {feedback}
            </div>
            {isRecording && (
                <div style={{
                    position: 'absolute', top: '10px', right: '10px',
                    color: '#fff', fontWeight: '600', fontSize: '0.78rem',
                    backgroundColor: 'rgba(239,68,68,0.85)', padding: '4px 10px',
                    borderRadius: '12px', backdropFilter: 'blur(8px)',
                }}>
                    REC
                </div>
            )}
        </div>
    );
};

export default LivePostureTracker;