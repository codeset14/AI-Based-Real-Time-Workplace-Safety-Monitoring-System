let video = document.getElementById("video");
let canvas = document.getElementById("canvas");
let output = document.getElementById("output");
let alertBox = document.getElementById("alert-box");
let stream;
let interval;

function startCamera() {
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(s => {
            stream = s;
            video.srcObject = stream;

            interval = setInterval(captureFrame, 1000); // 1 frame per second
        });
}

function stopCamera() {
    clearInterval(interval);
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
}

function captureFrame() {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    let ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0);

    let dataURL = canvas.toDataURL("image/jpeg");

    fetch("/detect", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ image: dataURL })
    })
    .then(response => response.json())
    .then(data => {
        output.src = "data:image/jpeg;base64," + data.image;

        if (data.violation) {
            alertBox.innerHTML = "⚠ SAFETY VIOLATION DETECTED";
            alertBox.className = "alert";
        } else {
            alertBox.innerHTML = "All Workers Safe";
            alertBox.className = "safe";
        }
    });
}