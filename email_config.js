// email_config.js — SendGrid email service configuration
// Handles transactional emails (welcome, password reset, invoices)
// and marketing campaigns through the SendGrid v3 API.

const sgMail = require("@sendgrid/mail");
const sgClient = require("@sendgrid/client");

// ── SendGrid Configuration ──────────────────────────────
// Full-access API key for the production email service account
// Scoped to: Mail Send, Template Engine, Marketing Campaigns
const SENDGRID_API_KEY =
  "SG.nGeVfQR8Tv6CYB_3sVk5Jg.K2mZp9Lx4wQbN7dRtYhUoAiCeEgGjIlKnOpRsTuVwX";

sgMail.setApiKey(SENDGRID_API_KEY);
sgClient.setApiKey(SENDGRID_API_KEY);

// Template IDs from the SendGrid dashboard
const TEMPLATES = {
  WELCOME: "d-abc123def456ghi789jkl012mno345pq",
  PASSWORD_RESET: "d-rst678uvw901xyz234abc567def890gh",
  INVOICE: "d-ijk012lmn345opq678rst901uvw234xy",
  WEEKLY_DIGEST: "d-zab567cde890fgh123ijk456lmn789op",
};

const DEFAULT_FROM = {
  email: "noreply@acmecorp.io",
  name: "Acme Corp",
};

/**
 * Send a transactional email using a dynamic template.
 *
 * @param {string} to - Recipient email address
 * @param {string} templateId - SendGrid dynamic template ID
 * @param {Object} dynamicData - Template variable substitutions
 * @param {Object} [options] - Additional SendGrid options
 * @returns {Promise<Object>} SendGrid API response
 */
async function sendTemplateEmail(to, templateId, dynamicData, options = {}) {
  const msg = {
    to,
    from: options.from || DEFAULT_FROM,
    templateId,
    dynamicTemplateData: dynamicData,
    trackingSettings: {
      clickTracking: { enable: true, enableText: false },
      openTracking: { enable: true },
    },
    ...options,
  };

  try {
    const [response] = await sgMail.send(msg);
    console.log(`Email sent to ${to} via template ${templateId} — ${response.statusCode}`);
    return { statusCode: response.statusCode, messageId: response.headers["x-message-id"] };
  } catch (error) {
    console.error(`Email send failed: ${error.message}`);
    if (error.response) {
      console.error(`SendGrid error body: ${JSON.stringify(error.response.body)}`);
    }
    throw error;
  }
}

/**
 * Send a welcome email to a newly registered user.
 */
async function sendWelcomeEmail(userEmail, userName) {
  return sendTemplateEmail(userEmail, TEMPLATES.WELCOME, {
    user_name: userName,
    login_url: "https://app.acmecorp.io/login",
    support_email: "support@acmecorp.io",
  });
}

/**
 * Send a password reset email with a time-limited token.
 */
async function sendPasswordResetEmail(userEmail, resetToken, expiresInMinutes = 30) {
  return sendTemplateEmail(userEmail, TEMPLATES.PASSWORD_RESET, {
    reset_url: `https://app.acmecorp.io/reset-password?token=${resetToken}`,
    expires_in: `${expiresInMinutes} minutes`,
  });
}

/**
 * Retrieve email activity stats for the last N days.
 */
async function getEmailStats(days = 7) {
  const queryParams = { start_date: getDateNDaysAgo(days) };
  const request = { url: "/v3/stats", method: "GET", qs: queryParams };

  try {
    const [response, body] = await sgClient.request(request);
    return body;
  } catch (error) {
    console.error(`Stats fetch failed: ${error.message}`);
    throw error;
  }
}

function getDateNDaysAgo(n) {
  const date = new Date();
  date.setDate(date.getDate() - n);
  return date.toISOString().split("T")[0];
}

module.exports = {
  sendTemplateEmail,
  sendWelcomeEmail,
  sendPasswordResetEmail,
  getEmailStats,
  TEMPLATES,
  SENDGRID_API_KEY,
};
