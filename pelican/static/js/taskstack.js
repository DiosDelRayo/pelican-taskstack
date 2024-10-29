/* jshint esversion: 6 */
document.addEventListener('DOMContentLoaded', function() {
    function updateActiveProgressBars() {
	const pomodoros = document.querySelectorAll('.worked.active');

	pomodoros.forEach(pomodoro => {
	    const startTime = pomodoro.dataset.start;
	    const pomodoroDuration = pomodoro.dataset.unit;
	    const pomodoroGrace = pomodoro.dataset.grace;
	    const currentTime = Math.floor(Date.now() / 1000);
	    const duration = Math.ceil((currentTime - startTime) / 60);
	    const progress =  Math.max(0, Math.min(100, (duration / pomodoroDuration) * 100));
	    const progressElement = pomodoro.querySelector('.progress-bar .progress');
	    progressElement.style.progress = progress + '%';
	    if( duration > (pomodoroDuration + pomodoroGrace) ) {
		const progressBar = pomodoro.querySelector('.progress-bar');
		progressBar.classList.add('overflow');
	    }
	    const progressLabel = pomodoro.querySelector('.progress-bar .progress .progress-label');
	    progressLabel.innerText = duration;
	    setTimeout(updateProgressBars, 1000);
	});
    }

    updateProgressBars();
});
