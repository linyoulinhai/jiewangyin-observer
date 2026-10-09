import {integer, sqliteTable, text, index, uniqueIndex} from 'drizzle-orm/sqlite-core';
export const profiles=sqliteTable('profiles',{
 id:text('id').primaryKey(),publicId:text('public_id').notNull(),nickname:text('nickname').notNull(),
 acceptedRules:text('accepted_rules').notNull().default(''),approvedTopics:integer('approved_topics').notNull().default(0),
 suspendedUntil:integer('suspended_until').notNull().default(0),created:integer('created').notNull()
},t=>[uniqueIndex('profiles_public_id').on(t.publicId)]);
export const topics=sqliteTable('topics',{
 id:text('id').primaryKey(),author:text('author').notNull().references(()=>profiles.id),title:text('title').notNull(),body:text('body').notNull(),category:text('category').notNull(),region:text('region').notNull().default(''),institution:text('institution').notNull().default(''),source:text('source').notNull().default(''),
 status:text('status').notNull().default('draft'),progress:text('progress').notNull().default('open'), requiresReview:integer('requires_review').notNull().default(0),allowExport:integer('allow_export').notNull().default(0),sensitive:integer('sensitive').notNull().default(0),reason:text('reason').notNull().default(''),slowSeconds:integer('slow_seconds').notNull().default(0),version:integer('version').notNull().default(1),created:integer('created').notNull(),updated:integer('updated').notNull(),published:integer('published')
},t=>[index('topics_status_updated').on(t.status,t.updated),index('topics_author_created').on(t.author,t.created)]);
export const replies=sqliteTable('replies',{
 id:text('id').primaryKey(),topic:text('topic').notNull().references(()=>topics.id),author:text('author').notNull().references(()=>profiles.id),parent:text('parent'),body:text('body').notNull(),source:text('source').notNull().default(''),status:text('status').notNull(),allowExport:integer('allow_export').notNull().default(0),reason:text('reason').notNull().default(''),created:integer('created').notNull(),updated:integer('updated').notNull()
},t=>[index('replies_topic_status_created').on(t.topic,t.status,t.created),index('replies_author_created').on(t.author,t.created)]);
export const attachments=sqliteTable('attachments',{
 id:text('id').primaryKey(),topic:text('topic').notNull().references(()=>topics.id),owner:text('owner').notNull().references(()=>profiles.id),name:text('name').notNull(),mime:text('mime').notNull(),size:integer('size').notNull(),storageKey:text('storage_key').notNull(),consentRules:text('consent_rules').notNull().default(''),visibility:text('visibility').notNull().default('private'),allowExport:integer('allow_export').notNull().default(0),source:text('source').notNull().default(''),status:text('status').notNull().default('uploading'),created:integer('created').notNull()
},t=>[index('attachments_topic').on(t.topic),index('attachments_owner').on(t.owner)]);
export const subscriptions=sqliteTable('subscriptions',{
 id:text('id').primaryKey(),user:text('user').notNull().references(()=>profiles.id),topic:text('topic').notNull().references(()=>topics.id)
},t=>[uniqueIndex('subscriptions_user_topic').on(t.user,t.topic),index('subscriptions_topic').on(t.topic)]);
export const notices=sqliteTable('notices',{
 id:text('id').primaryKey(),user:text('user').notNull().references(()=>profiles.id),topic:text('topic'),message:text('message').notNull(),isRead:integer('is_read').notNull().default(0),created:integer('created').notNull()
},t=>[index('notices_user_created').on(t.user,t.created)]);
export const cases=sqliteTable('cases',{
 id:text('id').primaryKey(),user:text('user').notNull().references(()=>profiles.id),kind:text('kind').notNull(),targetType:text('target_type').notNull(),targetId:text('target_id').notNull(),reason:text('reason').notNull(),details:text('details').notNull(),status:text('status').notNull().default('pending'),decision:text('decision').notNull().default(''),created:integer('created').notNull(),updated:integer('updated').notNull()
},t=>[index('cases_status_created').on(t.status,t.created),index('cases_user_created').on(t.user,t.created)]);
export const audit=sqliteTable('audit',{
 id:text('id').primaryKey(),moderator:text('moderator').notNull(),targetType:text('target_type').notNull(),targetId:text('target_id').notNull(),action:text('action').notNull(),reason:text('reason').notNull(),created:integer('created').notNull()
},t=>[index('audit_target_created').on(t.targetType,t.targetId,t.created)]);
export const limits=sqliteTable('limits',{
 key:text('key').primaryKey(),window:integer('window').notNull(),count:integer('count').notNull()
});

export const intake=sqliteTable('intake',{
 id:text('id').primaryKey(),owner:text('owner').notNull().default(''),receiptHash:text('receipt_hash').notNull(),kind:text('kind').notNull(),
 title:text('title').notNull(),institution:text('institution').notNull().default(''),region:text('region').notNull().default(''),
 body:text('body').notNull(),sourceNote:text('source_note').notNull().default(''),scope:text('scope').notNull().default('review'),
 rights:integer('rights').notNull().default(0),allowExport:integer('allow_export').notNull().default(0),status:text('status').notNull().default('draft'),
 decision:text('decision').notNull().default(''),version:integer('version').notNull().default(1),created:integer('created').notNull(),updated:integer('updated').notNull()
},t=>[index('intake_status_updated').on(t.status,t.updated),index('intake_owner_updated').on(t.owner,t.updated)]);
export const intakeFiles=sqliteTable('intake_files',{
 id:text('id').primaryKey(),intake:text('intake').notNull().references(()=>intake.id),name:text('name').notNull(),mime:text('mime').notNull(),
 size:integer('size').notNull(),storageKey:text('storage_key').notNull(),sha256:text('sha256').notNull(),publicAllowed:integer('public_allowed').notNull().default(0),
 exportAllowed:integer('export_allowed').notNull().default(0),status:text('status').notNull().default('ready'),created:integer('created').notNull()
},t=>[index('intake_files_intake').on(t.intake)]);
export const intakeEvents=sqliteTable('intake_events',{
 id:text('id').primaryKey(),intake:text('intake').notNull().references(()=>intake.id),action:text('action').notNull(),message:text('message').notNull(),created:integer('created').notNull()
},t=>[index('intake_events_intake').on(t.intake,t.created)]);
export const archiveRecords=sqliteTable('archive_records',{
 id:text('id').primaryKey(),intake:text('intake').notNull().references(()=>intake.id),name:text('name').notNull(),aliases:text('aliases').notNull().default(''),
 region:text('region').notNull().default(''),city:text('city').notNull().default(''),summary:text('summary').notNull(),body:text('body').notNull(),
 sources:text('sources').notNull(),verification:text('verification').notNull(),allowExport:integer('allow_export').notNull().default(0),
 status:text('status').notNull().default('published'),version:integer('version').notNull().default(1),created:integer('created').notNull(),updated:integer('updated').notNull()
},t=>[index('archive_status_updated').on(t.status,t.updated)]);
export const archiveMedia=sqliteTable('archive_media',{
 id:text('id').primaryKey(),record:text('record').notNull().references(()=>archiveRecords.id),file:text('file').notNull().references(()=>intakeFiles.id)
},t=>[uniqueIndex('archive_media_record_file').on(t.record,t.file)]);
