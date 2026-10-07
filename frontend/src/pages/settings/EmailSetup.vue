<template>
  <StaffLayout>
    <PageHeader
      title="Email Setup"
      subtitle="The outgoing mail server, and every email the recruitment process sends, stage by stage."
    />
    <div class="flex-1 overflow-y-auto bg-gray-50">
      <div v-if="loading && !setup" class="p-6 text-sm text-gray-500">Loading...</div>
      <EmptyState v-else-if="loadError" class="m-6" title="Could not load email settings" :description="loadError" />
      <div v-else-if="setup" class="flex flex-col gap-6 p-6">
        <!-- Mail server -->
        <SectionCard title="Outgoing Mail Server" icon="server" subtitle="The mailbox recruitment emails are sent from">
          <template #actions>
            <span
              class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold"
              :class="setup.account?.enabled ? 'bg-green-50 text-green-700' : 'bg-orange-50 text-orange-700'"
            >
              <FeatherIcon :name="setup.account?.enabled ? 'check-circle' : 'alert-circle'" class="h-3.5 w-3.5" />
              {{ setup.account?.enabled ? 'Connected' : 'Not set up: no emails are sent' }}
            </span>
          </template>

          <div class="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
            <div class="flex flex-col gap-4">
              <div class="flex flex-wrap items-center gap-2 text-sm">
                <span class="text-gray-600">Quick fill:</span>
                <Button v-for="p in PRESETS" :key="p.label" size="sm" variant="outline" @click="applyPreset(p)">{{ p.label }}</Button>
              </div>
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <FormControl label="Sender email" type="email" v-model="account.email_id" placeholder="recruitment@nls.ac.in" autocomplete="off" name="smtp-sender" />
                <FormControl label="Sender name" v-model="account.sender_name" placeholder="NLSIU Recruitment" />
                <FormControl label="SMTP server" v-model="account.smtp_server" placeholder="smtp.gmail.com" autocomplete="off" name="smtp-server" />
                <div class="grid grid-cols-2 gap-3">
                  <FormControl label="Port" type="number" v-model="account.smtp_port" />
                  <FormControl label="Security" type="select" v-model="account.security" :options="['STARTTLS', 'SSL', 'None']" />
                </div>
                <FormControl
                  label="Password / app password"
                  type="password"
                  v-model="account.password"
                  autocomplete="new-password"
                  name="smtp-password"
                  :placeholder="setup.account?.has_password ? '•••••••• saved; leave empty to keep' : ''"
                />
                <FormControl label="Login (if different from sender)" v-model="account.login_id" placeholder="Optional" autocomplete="off" name="smtp-login" />
              </div>
              <ErrorMessage :message="accountError" />
              <div class="flex flex-wrap items-center gap-2">
                <Button variant="solid" icon-left="save" :class="BTN_BRAND" :loading="savingAccount" @click="saveAccount">Save &amp; test connection</Button>
                <span class="text-xs text-gray-500">Saving logs in to the server; wrong details are reported here.</span>
              </div>
            </div>

            <div class="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm">
              <div class="mb-2 font-semibold text-gray-900">Reply-to address</div>
              <FormControl type="email" v-model="replyTo" placeholder="recruitment@nls.ac.in" autocomplete="off" name="reply-to" />
              <Button class="mt-2 w-full" variant="outline" :loading="savingReplyTo" @click="saveReplyTo">Save reply-to</Button>
              <p class="mt-1 mb-4 text-xs text-gray-500">Candidates' replies go here. Also usable in templates as {{ '{' + '{ contact_email }' + '}' }}.</p>
              <div class="mb-2 font-semibold text-gray-900">Send a test email</div>
              <FormControl type="email" v-model="testTo" placeholder="you@nls.ac.in" />
              <Button class="mt-2 w-full" variant="solid" icon-left="send" :class="BTN_DARK" :loading="sendingTest" :disabled="!setup.account" @click="sendTest">
                Send test
              </Button>
              <p class="mt-3 text-xs text-gray-500">
                Google Workspace / Gmail and Microsoft 365 need an <b>app password</b> (or SMTP enabled for the mailbox), not the
                normal login password.
              </p>
            </div>
          </div>
        </SectionCard>

        <!-- Emails by stage -->
        <SectionCard title="Emails by Stage" icon="mail" subtitle="Every email the recruitment process sends. Click a row to choose recipients and edit the wording">
          <template #actions>
            <Button size="sm" variant="solid" icon-left="plus" :class="BTN_BRAND" @click="newTemplate.open = true">New template</Button>
          </template>
          <DataTable
            :columns="RULE_COLUMNS"
            :rows="setup.rules"
            :filters="RULE_FILTERS"
            :selectable="false"
            clickable
            empty-title="No emails"
            search-placeholder="Search emails..."
            @row-click="openRule"
          >
            <template #cell-enabled="{ row }">
              <button
                type="button"
                role="switch"
                :aria-checked="!!row.enabled"
                :aria-label="`Send: ${row.label}`"
                class="relative block h-5 w-9 shrink-0 rounded-full transition"
                :class="row.enabled ? 'bg-brand-700' : 'bg-gray-300'"
                @click.stop="toggle(row)"
              >
                <span class="absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all" :class="row.enabled ? 'left-[18px]' : 'left-0.5'" />
              </button>
            </template>
            <template #cell-label="{ row }">
              <div class="min-w-[14rem]">
                <div class="font-semibold" :class="row.enabled ? 'text-gray-900' : 'text-gray-500'">{{ row.label }}</div>
                <div class="text-xs font-normal text-gray-500">{{ row.trigger_description }}</div>
              </div>
            </template>
            <template #cell-recipients="{ row }">
              <div class="flex min-w-[10rem] flex-wrap gap-1">
                <span v-for="r in recipientChips(row)" :key="r" class="rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-medium text-brand-700">{{ r }}</span>
                <span v-if="!recipientChips(row).length" class="rounded-full bg-red-50 px-2 py-0.5 text-[11px] font-medium text-red-700">No recipients</span>
                <span
                  v-else-if="row.empty_roles?.length"
                  class="rounded-full bg-orange-50 px-2 py-0.5 text-[11px] font-medium text-orange-800"
                  :title="`No user holds: ${row.empty_roles.join(', ')}. Assign the role in Roles & Permissions.`"
                >
                  No one holds {{ row.empty_roles.map((r) => r.replace(/^Pathways /, '')).join(', ') }}
                </span>
              </div>
            </template>
            <template #cell-sending="{ row }">
              <span
                class="whitespace-nowrap rounded px-1.5 py-0.5 text-[11px] font-medium"
                :class="row.is_automatic ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-600'"
              >{{ row.is_automatic ? 'Automatic' : 'When stage is built' }}</span>
            </template>
            <template #actions="{ row }">
              <div class="flex justify-end gap-1">
                <Button size="sm" variant="ghost" icon="eye" :aria-label="`View ${row.label}`" title="View" @click="openPreview(row)" />
                <Button size="sm" variant="ghost" icon="edit-2" :aria-label="`Edit ${row.label}`" title="Edit" @click="openRule(row)" />
                <Button size="sm" variant="ghost" icon="trash-2" class="!text-red-600" :aria-label="`Delete ${row.label}`" title="Delete" @click="askDelete(row)" />
              </div>
            </template>
          </DataTable>
        </SectionCard>

        <!-- Recent -->
        <SectionCard title="Recent Emails" icon="inbox" subtitle="The last 20 emails queued, with delivery status">
          <div v-if="!setup.recent.length" class="text-sm text-gray-500">No emails sent yet.</div>
          <div v-else class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="text-left text-xs uppercase text-gray-500">
                <tr>
                  <th class="py-2 pr-4">When</th>
                  <th class="py-2 pr-4">Subject</th>
                  <th class="py-2 pr-4">To</th>
                  <th class="py-2">Status</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-for="row in setup.recent" :key="row.name" class="align-top">
                  <td class="whitespace-nowrap py-2 pr-4 text-gray-500">{{ formatDateTime(row.creation) }}</td>
                  <td class="py-2 pr-4 text-gray-900">{{ row.subject }}</td>
                  <td class="py-2 pr-4 text-gray-700">{{ row.recipients }}</td>
                  <td class="py-2">
                    <StatusBadge :status="row.status === 'Sent' ? 'Completed' : row.status === 'Error' ? 'Rejected' : 'Pending'" />
                    <span class="ml-1 text-xs text-gray-500">{{ row.status }}</span>
                    <div v-if="row.error" class="mt-1 text-xs text-red-700">{{ row.error }}</div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </SectionCard>
      </div>
    </div>

    <Dialog v-model="newTemplate.open" :options="{ title: 'New Email Template', size: '5xl' }">
      <template #body-content>
        <div class="flex flex-col gap-3">
          <FormControl label="Template name" v-model="newTemplate.name" placeholder="e.g. Offer Letter Covering Note" />
          <FormControl label="Subject" v-model="newTemplate.subject" placeholder="Offer of appointment: {{ job_title }}" />
          <div>
            <span class="mb-1.5 block text-sm text-gray-700">Message</span>
            <TextEditor
              :content="newTemplate.response"
              :fixed-menu="true"
              editor-class="prose-sm max-w-none min-h-[22rem] px-3 py-2"
              class="rounded border border-gray-300 bg-white"
              @change="(html) => (newTemplate.response = html)"
            />
          </div>
          <ErrorMessage :message="newTemplate.error" />
        </div>
      </template>
      <template #actions>
        <Button variant="solid" :class="BTN_BRAND" :loading="newTemplate.saving" @click="createTemplate">Create template</Button>
      </template>
    </Dialog>

    <Dialog v-model="preview.open" :options="{ size: '4xl' }">
      <template #body>
        <div class="flex max-h-[85vh] flex-col">
          <header class="flex shrink-0 items-start justify-between gap-3 bg-brand-700 px-6 py-4 text-white">
            <div class="min-w-0">
              <div class="text-xs font-semibold uppercase tracking-wider text-white/75">Preview · sample data from a recent job</div>
              <h2 class="truncate text-lg font-bold">{{ preview.data?.label || 'Email' }}</h2>
            </div>
            <button class="rounded-md p-1.5 text-white/80 hover:bg-white/15 hover:text-white" aria-label="Close" @click="preview.open = false">
              <FeatherIcon name="x" class="h-5 w-5" />
            </button>
          </header>
          <div class="min-h-0 flex-1 overflow-y-auto">
            <div v-if="preview.loading" class="px-6 py-10 text-sm text-gray-500">Loading...</div>
            <div v-else-if="preview.error" class="px-6 py-6 text-sm text-red-700">{{ preview.error }}</div>
            <template v-else-if="preview.data">
              <dl class="grid grid-cols-[6rem_minmax(0,1fr)] gap-x-4 gap-y-2 border-b bg-gray-50 px-6 py-4 text-sm">
                <dt class="text-gray-500">To</dt>
                <dd class="text-gray-900">
                  {{ preview.data.recipient_groups.join(', ') || 'No recipients' }}
                  <span v-if="preview.data.recipients.length" class="block text-xs text-gray-500">
                    e.g. {{ preview.data.recipients.slice(0, 4).map((r) => r.email).join(', ') }}<template v-if="preview.data.recipients.length > 4"> …</template>
                  </span>
                </dd>
                <template v-if="preview.data.cc">
                  <dt class="text-gray-500">CC</dt>
                  <dd class="text-gray-900">{{ preview.data.cc }}</dd>
                </template>
                <dt class="text-gray-500">Subject</dt>
                <dd class="font-semibold text-gray-900">{{ preview.data.subject }}</dd>
                <dt class="text-gray-500">Template</dt>
                <dd class="text-gray-700">{{ preview.data.template }}</dd>
                <template v-if="preview.data.attachments.length || preview.data.attach_record_files">
                  <dt class="text-gray-500">Attachments</dt>
                  <dd class="text-gray-700">
                    {{ [...preview.data.attachments, preview.data.attach_record_files ? "the record's own files" : null].filter(Boolean).join(', ') }}
                  </dd>
                </template>
              </dl>
              <div class="prose prose-sm max-w-none px-6 py-5" v-html="preview.data.message" />
            </template>
          </div>
          <footer class="flex shrink-0 justify-between gap-2 border-t px-6 py-3">
            <span class="self-center text-xs text-gray-500">
              {{ preview.data && !preview.data.enabled ? 'This email is switched off.' : '' }}
            </span>
            <Button variant="solid" icon-left="edit-2" :class="BTN_BRAND" @click="editFromPreview">Edit</Button>
          </footer>
        </div>
      </template>
    </Dialog>

    <Dialog
      v-model="del.open"
      :options="{
        title: `Delete “${del.rule?.label}”?`,
        message: 'This email will no longer be sent and cannot be brought back from here. Its template is kept. To pause it instead, use the On switch.',
        size: 'md',
      }"
    >
      <template #actions>
        <div class="flex gap-2">
          <Button variant="outline" @click="del.open = false">Cancel</Button>
          <Button variant="solid" icon-left="trash-2" class="!bg-red-700 !text-white hover:!bg-red-800" :loading="del.saving" @click="confirmDelete">Delete</Button>
        </div>
      </template>
    </Dialog>

    <!-- Edit one email -->
    <Dialog v-model="edit.open" :options="{ title: edit.rule?.label || 'Email', size: '5xl' }">
      <template #body-content>
        <div v-if="edit.rule" class="flex flex-col gap-5">
          <p class="text-sm text-gray-600">{{ edit.rule.trigger_description }}</p>
          <label class="flex items-center gap-2 text-sm font-medium text-gray-900">
            <input v-model="edit.form.enabled" type="checkbox" class="rounded border-gray-300" /> Send this email
          </label>

          <div>
            <div class="mb-2 text-xs font-bold uppercase tracking-wide text-brand-700">Recipients</div>
            <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div class="flex flex-col gap-2 text-sm">
                <label class="flex items-center gap-2"><input v-model="edit.form.send_to_candidate" type="checkbox" class="rounded border-gray-300" /> The candidate</label>
                <label class="flex items-center gap-2"><input v-model="edit.form.send_to_committee" type="checkbox" class="rounded border-gray-300" /> The job's shortlisting committee</label>
                <label class="flex items-center gap-2"><input v-model="edit.form.send_to_approvers" type="checkbox" class="rounded border-gray-300" /> The approvers of the current step</label>
              </div>
              <div>
                <div class="mb-1 text-sm text-gray-700">Everyone with these roles</div>
                <div class="max-h-36 overflow-y-auto rounded border p-2 text-sm">
                  <label v-for="r in setup.role_options" :key="r" class="flex items-center gap-2">
                    <input v-model="edit.form.recipient_roles" type="checkbox" :value="r" class="rounded border-gray-300" /> {{ r.replace(/^Pathways /, '') }}
                  </label>
                </div>
              </div>
              <FormControl label="Also send to (emails, comma separated)" v-model="edit.form.extra_recipients" placeholder="comms@nls.ac.in" />
              <FormControl label="CC (emails, comma separated)" v-model="edit.form.cc" />
            </div>
          </div>

          <div>
            <div class="mb-2 text-xs font-bold uppercase tracking-wide text-brand-700">Content</div>
            <div class="mb-3 flex flex-wrap items-end gap-2">
              <FormControl
                class="min-w-[16rem] flex-1"
                label="Email template"
                type="select"
                :model-value="edit.form.email_template"
                :options="templateOptions"
                @update:model-value="pickTemplate"
              />
              <Button variant="ghost" icon="refresh-cw" aria-label="Refresh the template list" @click="reload" />
            </div>
            <p class="-mt-1 mb-3 text-xs text-gray-500">
              Lists every Email Template, including ones added in Desk or with <b>New template</b> on the page.
              <template v-if="usedBy(edit.form.email_template).length > 1">
                <b>Shared:</b> this template is also used by {{ usedBy(edit.form.email_template).filter((l) => l !== edit.rule.label).join(', ') }};
                editing it below changes those too.
              </template>
              <template v-else>Editing the subject or message below changes this template.</template>
            </p>
            <FormControl label="Subject" v-model="edit.form.subject" />
            <div class="mt-3">
              <span class="mb-1.5 block text-sm text-gray-700">Message</span>
              <TextEditor
                :key="`${edit.rule.name}-${edit.editorKey}`"
                :content="edit.form.response"
                :fixed-menu="true"
                editor-class="prose-sm max-w-none min-h-[20rem] px-3 py-2"
                class="rounded border border-gray-300 bg-white"
                @change="(html) => (edit.form.response = html)"
              />
            </div>
            <div class="mt-2 flex flex-wrap items-center gap-1.5 text-xs">
              <span class="text-gray-500">Placeholders (click to copy):</span>
              <button
                v-for="v in variables(edit.rule)"
                :key="v"
                type="button"
                class="rounded bg-gray-100 px-1.5 py-0.5 font-mono text-gray-700 hover:bg-brand-50 hover:text-brand-700"
                @click="copy(placeholder(v))"
                v-text="placeholder(v)"
              />
            </div>
          </div>
          <div>
            <div class="mb-2 text-xs font-bold uppercase tracking-wide text-brand-700">Attachments</div>
            <ul v-if="edit.rule.attachments?.length" class="mb-2 flex flex-col gap-1.5">
              <li v-for="f in edit.rule.attachments" :key="f.name" class="flex items-center justify-between gap-2 rounded-md border px-3 py-1.5 text-sm">
                <a :href="f.file_url" target="_blank" class="flex min-w-0 items-center gap-2 text-gray-800 hover:text-brand-700">
                  <FeatherIcon name="paperclip" class="h-3.5 w-3.5 shrink-0" /><span class="truncate">{{ f.file_name }}</span>
                </a>
                <Button size="sm" variant="ghost" icon="x" :aria-label="`Remove ${f.file_name}`" @click="removeAttachment(f)" />
              </li>
            </ul>
            <FileUploader
              :upload-args="{ doctype: 'Recruitment Email Rule', docname: edit.rule.name, private: true }"
              @success="attachmentAdded"
            >
              <template #default="{ openFileSelector, uploading }">
                <Button size="sm" icon-left="upload" :loading="uploading" @click="openFileSelector">Attach a file to every email</Button>
              </template>
            </FileUploader>
            <label class="mt-3 flex items-start gap-2 text-sm text-gray-800">
              <input v-model="edit.form.attach_record_files" type="checkbox" class="mt-0.5 rounded border-gray-300" />
              <span>
                Also attach the record's own files
                <span class="block text-xs text-gray-500">
                  e.g. the generated / signed appointment order on the Offer, so each candidate gets their own letter.
                </span>
              </span>
            </label>
          </div>
          <ErrorMessage :message="edit.error" />
        </div>
      </template>
      <template #actions>
        <Button variant="solid" :class="BTN_BRAND" :loading="edit.saving" @click="saveRule">Save</Button>
      </template>
    </Dialog>
  </StaffLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Button, Dialog, ErrorMessage, FeatherIcon, FileUploader, FormControl, TextEditor } from 'frappe-ui'
import dayjs from 'dayjs'
import StaffLayout from '@/layouts/StaffLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import SectionCard from '@/components/common/SectionCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import DataTable from '@/components/common/DataTable.vue'
import { BTN_BRAND, BTN_DARK } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'
import { emailSetupService } from '@/services/emailSetup'

const PRESETS = [
  { label: 'Google Workspace / Gmail', smtp_server: 'smtp.gmail.com', smtp_port: 587, security: 'STARTTLS' },
  { label: 'Microsoft 365', smtp_server: 'smtp.office365.com', smtp_port: 587, security: 'STARTTLS' },
  { label: 'Zoho', smtp_server: 'smtp.zoho.in', smtp_port: 587, security: 'STARTTLS' },
]

const RULE_COLUMNS = [
  { key: 'enabled', label: 'On', sortable: false },
  { key: 'label', label: 'Email', format: (r) => `${r.label} ${r.trigger_description || ''}` },
  { key: 'stage', label: 'Stage' },
  { key: 'recipients', label: 'Recipients', sortable: false, format: (r) => recipientChips(r).join(', ') },
  { key: 'email_template', label: 'Template' },
  { key: 'sending', label: 'Sending', sortable: false, format: (r) => (r.is_automatic ? 'Automatic' : 'When stage is built') },
]
const RULE_FILTERS = [{ key: 'stage', label: 'Stages' }]

const setup = ref(null)
const loading = ref(false)
const loadError = ref('')

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    setup.value = await emailSetupService.getSetup()
    fillAccount()
    replyTo.value = setup.value.reply_to || ''
  } catch (e) {
    loadError.value = e?.messages?.[0] || 'Only administrators can change email settings.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

// ----- mail server
const account = reactive({ email_id: '', sender_name: '', smtp_server: '', smtp_port: 587, security: 'STARTTLS', password: '', login_id: '' })
const accountError = ref('')
const savingAccount = ref(false)

function fillAccount() {
  const a = setup.value?.account || {}
  Object.assign(account, {
    email_id: a.email_id || '',
    sender_name: a.sender_name && a.sender_name !== 'Pathways Outgoing' ? a.sender_name : 'NLSIU Recruitment',
    smtp_server: a.smtp_server || '',
    smtp_port: a.smtp_port || 587,
    security: a.security || 'STARTTLS',
    password: '',
    login_id: a.login_id || '',
  })
}

function applyPreset(p) {
  Object.assign(account, { smtp_server: p.smtp_server, smtp_port: p.smtp_port, security: p.security })
}

async function saveAccount() {
  savingAccount.value = true
  accountError.value = ''
  try {
    setup.value.account = await emailSetupService.saveAccount({ ...account })
    account.password = ''
    toast({ title: 'Mail server connected and saved.', icon: 'check', iconClasses: 'text-green-500' })
  } catch (e) {
    accountError.value = e?.messages?.[0] || 'Could not connect to the mail server. Check the details and the password.'
  } finally {
    savingAccount.value = false
  }
}

const replyTo = ref('')
const savingReplyTo = ref(false)
async function saveReplyTo() {
  savingReplyTo.value = true
  try {
    replyTo.value = await emailSetupService.saveReplyTo(replyTo.value)
    toast({ title: replyTo.value ? `Replies will go to ${replyTo.value}.` : 'Reply-to cleared.', icon: 'check', iconClasses: 'text-green-500' })
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not save it.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    savingReplyTo.value = false
  }
}

const testTo = ref('')
const sendingTest = ref(false)
async function sendTest() {
  sendingTest.value = true
  try {
    await emailSetupService.sendTest(testTo.value)
    toast({ title: `Test email sent to ${testTo.value}.`, icon: 'check', iconClasses: 'text-green-500' })
    setup.value = await emailSetupService.getSetup()
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'The test email could not be sent.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    sendingTest.value = false
  }
}

// ----- rules by stage
function recipientChips(rule) {
  return [
    rule.send_to_candidate && 'Candidate',
    rule.send_to_committee && 'Shortlisting committee',
    rule.send_to_approvers && 'Current approvers',
    ...(rule.recipient_roles || []).map((r) => r.replace(/^Pathways /, '')),
    ...(rule.extra_recipients || '').split(',').map((e) => e.trim()).filter(Boolean),
  ].filter(Boolean)
}

// Jinja placeholder as it goes into a template (built here: Vue would read
// the braces in the template as its own interpolation).
function placeholder(name) {
  return `{{ ${name} }}`
}

function variables(rule) {
  return (rule?.variables || '').split(',').map((v) => v.trim()).filter(Boolean)
}

// ----- view
const preview = reactive({ open: false, loading: false, error: '', data: null, rule: null })

async function openPreview(rule) {
  Object.assign(preview, { open: true, loading: true, error: '', data: null, rule })
  try {
    preview.data = await emailSetupService.previewRule(rule.name)
  } catch (e) {
    preview.error = e?.messages?.[0] || 'Could not build the preview.'
  } finally {
    preview.loading = false
  }
}

function editFromPreview() {
  preview.open = false
  openRule(preview.rule)
}

// ----- delete
const del = reactive({ open: false, rule: null, saving: false })

function askDelete(rule) {
  Object.assign(del, { open: true, rule })
}

async function confirmDelete() {
  del.saving = true
  try {
    setup.value = await emailSetupService.deleteRule(del.rule.name)
    toast({ title: `“${del.rule.label}” deleted.`, icon: 'check', iconClasses: 'text-green-500' })
    del.open = false
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not delete it.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  } finally {
    del.saving = false
  }
}

async function toggle(rule) {
  const next = rule.enabled ? 0 : 1
  rule.enabled = next
  try {
    await emailSetupService.toggleRule(rule.name, next)
    toast({ title: `${rule.label}: ${next ? 'on' : 'off'}.`, icon: 'check', iconClasses: 'text-green-500' })
  } catch (e) {
    rule.enabled = next ? 0 : 1
    toast({ title: e?.messages?.[0] || 'Could not change it.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  }
}

const edit = reactive({ open: false, rule: null, form: {}, saving: false, error: '', editorKey: 0 })

function openRule(rule) {
  Object.assign(edit, {
    open: true,
    rule,
    error: '',
    form: {
      enabled: !!rule.enabled,
      send_to_candidate: !!rule.send_to_candidate,
      send_to_committee: !!rule.send_to_committee,
      send_to_approvers: !!rule.send_to_approvers,
      recipient_roles: [...(rule.recipient_roles || [])],
      extra_recipients: rule.extra_recipients || '',
      cc: rule.cc || '',
      subject: rule.subject || '',
      response: rule.response || '',
      email_template: rule.email_template,
      attach_record_files: !!rule.attach_record_files,
    },
  })
}

function usedBy(name) {
  return (setup.value?.templates || []).find((t) => t.name === name)?.used_by || []
}

const templateOptions = computed(() => (setup.value?.templates || []).map((t) => ({ label: t.name, value: t.name })))

// Switching template loads its wording into the editor (saved on Save).
function pickTemplate(name) {
  const t = (setup.value?.templates || []).find((x) => x.name === name)
  if (!t) return
  Object.assign(edit.form, { email_template: name, subject: t.subject || '', response: t.response || '' })
  edit.editorKey++
}

async function reload() {
  setup.value = await emailSetupService.getSetup()
  if (edit.rule) edit.rule = setup.value.rules.find((r) => r.name === edit.rule.name) || edit.rule
  toast({ title: 'Templates refreshed.', icon: 'check', iconClasses: 'text-green-500' })
}

function attachmentAdded() {
  emailSetupService.getSetup().then((data) => {
    setup.value = data
    edit.rule = data.rules.find((r) => r.name === edit.rule.name) || edit.rule
  })
}

async function removeAttachment(file) {
  try {
    setup.value = await emailSetupService.removeAttachment(edit.rule.name, file.name)
    edit.rule = setup.value.rules.find((r) => r.name === edit.rule.name) || edit.rule
  } catch (e) {
    toast({ title: e?.messages?.[0] || 'Could not remove the file.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  }
}

const newTemplate = reactive({ open: false, name: '', subject: '', response: '', saving: false, error: '' })

async function createTemplate() {
  newTemplate.saving = true
  newTemplate.error = ''
  try {
    setup.value = await emailSetupService.createTemplate(newTemplate.name, newTemplate.subject, newTemplate.response)
    toast({ title: `Template "${newTemplate.name}" created.`, icon: 'check', iconClasses: 'text-green-500' })
    Object.assign(newTemplate, { open: false, name: '', subject: '', response: '' })
  } catch (e) {
    newTemplate.error = e?.messages?.[0] || 'Could not create the template.'
  } finally {
    newTemplate.saving = false
  }
}

async function saveRule() {
  edit.saving = true
  edit.error = ''
  try {
    const f = edit.form
    setup.value = await emailSetupService.saveRule(edit.rule.name, {
      ...f,
      enabled: f.enabled ? 1 : 0,
      attach_record_files: f.attach_record_files ? 1 : 0,
      send_to_candidate: f.send_to_candidate ? 1 : 0,
      send_to_committee: f.send_to_committee ? 1 : 0,
      send_to_approvers: f.send_to_approvers ? 1 : 0,
    })
    edit.open = false
    toast({ title: 'Email saved.', icon: 'check', iconClasses: 'text-green-500' })
  } catch (e) {
    edit.error = e?.messages?.[0] || 'Could not save.'
  } finally {
    edit.saving = false
  }
}

async function copy(text) {
  try {
    await navigator.clipboard.writeText(text)
    toast({ title: `Copied ${text}`, icon: 'check', iconClasses: 'text-green-500' })
  } catch {
    // clipboard unavailable
  }
}

function formatDateTime(value) {
  return dayjs(value).format('DD MMM, h:mm A')
}
</script>
