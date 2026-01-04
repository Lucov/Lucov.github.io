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

      // Validate data freshness - only show if updated within last 48 hours
      if (!this.isDataFresh(data)) {
        console.warn('Health data is stale or missing');
        this.hideHealthStats();
        return;
      }

      // Validate that we have at least some real data
      if (!this.hasValidData(data)) {
        console.warn('No valid health data available');
        this.hideHealthStats();
        return;
      }

      this.renderStats(data);
    } catch (error) {
      console.error('Error loading health data:', error);
      this.hideHealthStats();
    }
  }

  isDataFresh(data) {
    if (!data.lastUpdated) {
      return false;
    }

    const lastUpdate = new Date(data.lastUpdated);
    const now = new Date();
    const hoursSinceUpdate = (now - lastUpdate) / (1000 * 60 * 60);

    // Data must be updated within last 48 hours (2 days)
    const isRecent = hoursSinceUpdate <= 48;

    if (!isRecent) {
      console.log(`Health data is ${Math.round(hoursSinceUpdate)} hours old (max: 48 hours)`);
    }

    return isRecent;
  }

  hasValidData(data) {
    // Check if we have any actual data fields
    const dailyStats = data.dailyStats || {};

    const hasSleep = dailyStats.sleep?.score != null;
    const hasHeartRate = dailyStats.heartRate?.resting != null;
    const hasActivity = dailyStats.activity?.steps != null;
    const hasEnergy = dailyStats.energy?.score != null;

    // Must have at least one valid data field
    return hasSleep || hasHeartRate || hasActivity || hasEnergy;
  }

  hideHealthStats() {
    // Hide the entire health stats card when no valid data is available
    if (this.container) {
      this.container.style.display = 'none';
    }
  }

  getSleepQuality(score) {
    if (score >= 80) return { text: 'Excellent', color: '#10b981' };
    if (score >= 70) return { text: 'Good', color: '#3b82f6' };
    if (score >= 60) return { text: 'Fair', color: '#f59e0b' };
    return { text: 'Poor', color: '#ef4444' };
  }

  getEnergyLevel(score) {
    if (score >= 80) return { text: 'High Energy', color: '#10b981' };
    if (score >= 70) return { text: 'Good', color: '#3b82f6' };
    if (score >= 60) return { text: 'Moderate', color: '#f59e0b' };
    return { text: 'Low', color: '#ef4444' };
  }

  getHeartRateStatus(resting) {
    if (resting < 60) return { text: 'Athletic', color: '#10b981' };
    if (resting <= 70) return { text: 'Excellent', color: '#3b82f6' };
    if (resting <= 80) return { text: 'Good', color: '#f59e0b' };
    return { text: 'Above Average', color: '#ef4444' };
  }

  getStressLevel(average) {
    if (average <= 25) return { text: 'Very Low', color: '#10b981' };
    if (average <= 50) return { text: 'Low', color: '#3b82f6' };
    if (average <= 75) return { text: 'Moderate', color: '#f59e0b' };
    return { text: 'High', color: '#ef4444' };
  }

  formatTime(hours) {
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    return `${h}h ${m}m`;
  }

  renderStats(data) {
    const { dailyStats, weeklyTrends, lastUpdated } = data;

    // Safely check for available data
    const hasSleep = dailyStats?.sleep?.score != null;
    const hasEnergy = dailyStats?.energy?.score != null;
    const hasHeartRate = dailyStats?.heartRate?.resting != null;
    const hasActivity = dailyStats?.activity?.steps != null;
    const hasStress = dailyStats?.stress?.average != null;

    const sleepQuality = hasSleep ? this.getSleepQuality(dailyStats.sleep.score) : null;
    const energyLevel = hasEnergy ? this.getEnergyLevel(dailyStats.energy.score) : null;
    const hrStatus = hasHeartRate ? this.getHeartRateStatus(dailyStats.heartRate.resting) : null;
    const stressLevel = hasStress ? this.getStressLevel(dailyStats.stress.average) : null;

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
        ${hasSleep ? `
        <div class="health-stat">
          <div class="stat-icon">😴</div>
          <div class="stat-content">
            <div class="stat-label">Sleep Score</div>
            <div class="stat-value" style="color: ${sleepQuality.color}">${dailyStats.sleep.score}</div>
            <div class="stat-meta">${sleepQuality.text} • ${this.formatTime(dailyStats.sleep.duration)}</div>
            ${dailyStats.sleep.deepSleep != null && dailyStats.sleep.remSleep != null ? `
            <div class="stat-detail">
              <span>Deep: ${this.formatTime(dailyStats.sleep.deepSleep)}</span>
              <span>REM: ${this.formatTime(dailyStats.sleep.remSleep)}</span>
            </div>
            ` : ''}
          </div>
        </div>
        ` : ''}

        ${hasEnergy ? `
        <div class="health-stat">
          <div class="stat-icon">⚡</div>
          <div class="stat-content">
            <div class="stat-label">Energy Score</div>
            <div class="stat-value" style="color: ${energyLevel.color}">${dailyStats.energy.score}</div>
            <div class="stat-meta">${energyLevel.text}</div>
          </div>
        </div>
        ` : ''}

        ${hasHeartRate ? `
        <div class="health-stat">
          <div class="stat-icon">❤️</div>
          <div class="stat-content">
            <div class="stat-label">Resting Heart Rate</div>
            <div class="stat-value" style="color: ${hrStatus.color}">${dailyStats.heartRate.resting} <span class="unit">bpm</span></div>
            <div class="stat-meta">${hrStatus.text}</div>
            ${dailyStats.heartRate.average ? `<div class="stat-detail">Avg: ${dailyStats.heartRate.average} bpm</div>` : ''}
          </div>
        </div>
        ` : ''}

        ${hasActivity ? `
        <div class="health-stat">
          <div class="stat-icon">👟</div>
          <div class="stat-content">
            <div class="stat-label">Steps</div>
            <div class="stat-value">${dailyStats.activity.steps.toLocaleString()}</div>
            ${dailyStats.activity.activeMinutes ? `<div class="stat-meta">${dailyStats.activity.activeMinutes} active min</div>` : ''}
            ${dailyStats.activity.calories ? `<div class="stat-detail">${dailyStats.activity.calories} cal</div>` : ''}
          </div>
        </div>
        ` : ''}

        ${hasStress ? `
        <div class="health-stat">
          <div class="stat-icon">🧘</div>
          <div class="stat-content">
            <div class="stat-label">Stress Level</div>
            <div class="stat-value" style="color: ${stressLevel.color}">${dailyStats.stress.average} <span class="unit">/100</span></div>
            <div class="stat-meta">${stressLevel.text}</div>
          </div>
        </div>
        ` : ''}
      </div>

      ${weeklyTrends ? `
      <div class="health-trends">
        <div class="trend-title">7-Day Averages</div>
        <div class="trend-grid">
          ${weeklyTrends.averageSleepScore != null ? `
          <div class="trend-item">
            <span class="trend-label">Sleep Score</span>
            <span class="trend-value">${weeklyTrends.averageSleepScore}</span>
          </div>
          ` : ''}
          ${weeklyTrends.averageEnergyScore != null ? `
          <div class="trend-item">
            <span class="trend-label">Energy Score</span>
            <span class="trend-value">${weeklyTrends.averageEnergyScore}</span>
          </div>
          ` : ''}
          ${weeklyTrends.averageSleepDuration != null ? `
          <div class="trend-item">
            <span class="trend-label">Sleep Duration</span>
            <span class="trend-value">${this.formatTime(weeklyTrends.averageSleepDuration)}</span>
          </div>
          ` : ''}
          ${weeklyTrends.averageRestingHR != null ? `
          <div class="trend-item">
            <span class="trend-label">Resting HR</span>
            <span class="trend-value">${weeklyTrends.averageRestingHR} bpm</span>
          </div>
          ` : ''}
          ${weeklyTrends.averageSteps != null ? `
          <div class="trend-item">
            <span class="trend-label">Daily Steps</span>
            <span class="trend-value">${weeklyTrends.averageSteps.toLocaleString()}</span>
          </div>
          ` : ''}
        </div>
      </div>
      ` : ''}
    `;
  }

}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const healthStats = new HealthStats();
  healthStats.loadData();
});
