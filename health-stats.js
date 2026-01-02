// Health Stats Display
class HealthStats {
  constructor() {
    this.dataUrl = 'health-data.json';
    this.container = document.getElementById('health-stats-card');
  }

  async loadData() {
    try {
      const response = await fetch(this.dataUrl);
      if (!response.ok) throw new Error('Failed to load health data');
      const data = await response.json();
      this.renderStats(data);
    } catch (error) {
      console.error('Error loading health data:', error);
      this.renderError();
    }
  }

  getSleepQuality(score) {
    if (score >= 80) return { text: 'Excellent', color: '#10b981' };
    if (score >= 70) return { text: 'Good', color: '#3b82f6' };
    if (score >= 60) return { text: 'Fair', color: '#f59e0b' };
    return { text: 'Poor', color: '#ef4444' };
  }

  getHeartRateStatus(resting) {
    if (resting < 60) return { text: 'Athletic', color: '#10b981' };
    if (resting <= 70) return { text: 'Excellent', color: '#3b82f6' };
    if (resting <= 80) return { text: 'Good', color: '#f59e0b' };
    return { text: 'Above Average', color: '#ef4444' };
  }

  formatTime(hours) {
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    return `${h}h ${m}m`;
  }

  renderStats(data) {
    const { dailyStats, weeklyTrends, lastUpdated } = data;
    const sleepQuality = this.getSleepQuality(dailyStats.sleep.score);
    const hrStatus = this.getHeartRateStatus(dailyStats.heartRate.resting);

    const updateDate = new Date(lastUpdated).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });

    this.container.innerHTML = `
      <div class="health-header">
        <h3>📊 Today's Health Stats</h3>
        <span class="last-updated">Updated: ${updateDate}</span>
      </div>

      <div class="health-grid">
        <div class="health-stat primary">
          <div class="stat-icon">😴</div>
          <div class="stat-content">
            <div class="stat-label">Sleep Score</div>
            <div class="stat-value" style="color: ${sleepQuality.color}">${dailyStats.sleep.score}</div>
            <div class="stat-meta">${sleepQuality.text} • ${this.formatTime(dailyStats.sleep.duration)}</div>
            <div class="stat-detail">
              <span>Deep: ${this.formatTime(dailyStats.sleep.deepSleep)}</span>
              <span>REM: ${this.formatTime(dailyStats.sleep.remSleep)}</span>
            </div>
          </div>
        </div>

        <div class="health-stat">
          <div class="stat-icon">❤️</div>
          <div class="stat-content">
            <div class="stat-label">Resting Heart Rate</div>
            <div class="stat-value" style="color: ${hrStatus.color}">${dailyStats.heartRate.resting} <span class="unit">bpm</span></div>
            <div class="stat-meta">${hrStatus.text}</div>
            <div class="stat-detail">Avg: ${dailyStats.heartRate.average} bpm</div>
          </div>
        </div>

        <div class="health-stat">
          <div class="stat-icon">👟</div>
          <div class="stat-content">
            <div class="stat-label">Steps</div>
            <div class="stat-value">${dailyStats.activity.steps.toLocaleString()}</div>
            <div class="stat-meta">${dailyStats.activity.activeMinutes} active min</div>
            <div class="stat-detail">${dailyStats.activity.calories} cal</div>
          </div>
        </div>

        <div class="health-stat">
          <div class="stat-icon">🧘</div>
          <div class="stat-content">
            <div class="stat-label">Stress Level</div>
            <div class="stat-value">${dailyStats.stress.average} <span class="unit">/100</span></div>
            <div class="stat-meta">${dailyStats.stress.level}</div>
          </div>
        </div>
      </div>

      <div class="health-trends">
        <div class="trend-title">7-Day Averages</div>
        <div class="trend-grid">
          <div class="trend-item">
            <span class="trend-label">Sleep Score</span>
            <span class="trend-value">${weeklyTrends.averageSleepScore}</span>
          </div>
          <div class="trend-item">
            <span class="trend-label">Sleep Duration</span>
            <span class="trend-value">${this.formatTime(weeklyTrends.averageSleepDuration)}</span>
          </div>
          <div class="trend-item">
            <span class="trend-label">Resting HR</span>
            <span class="trend-value">${weeklyTrends.averageRestingHR} bpm</span>
          </div>
          <div class="trend-item">
            <span class="trend-label">Daily Steps</span>
            <span class="trend-value">${weeklyTrends.averageSteps.toLocaleString()}</span>
          </div>
        </div>
      </div>
    `;
  }

  renderError() {
    this.container.innerHTML = `
      <div class="health-error">
        <p>Unable to load health data. Please check back later.</p>
      </div>
    `;
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const healthStats = new HealthStats();
  healthStats.loadData();
});
