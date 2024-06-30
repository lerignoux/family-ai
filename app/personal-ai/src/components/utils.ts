export function playAudio(audioBlob: Blob) {
  const objectURL = URL.createObjectURL(audioBlob);
  const newAudioURL = objectURL;
  const w = new Audio();
  w.src = newAudioURL;
  w.play();
}
